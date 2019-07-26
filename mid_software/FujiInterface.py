#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import serial
import struct
import math
import sys
from crc_algorithms import Crc
import serialComm
from EA_RCcmd import EA_RCcmd
from EAMIDexception import EAMIDexception

# TODO: fold some of this into a general MODBUS class
# TODO: add CRC check when processing replies
# TODO: add exceptions

class FujiPXR4Cmd:
	"""blah blah blah"""
	def __init__(self,slaveAddy,functionCode):
		self.slaveAddy = slaveAddy
		self.functionCode = functionCode
		self.rplyFunctionCode = 0
		self.crc = Crc(width=16,poly=0x8005,reflect_in=True,
					   xor_in=0xFFFF,reflect_out=True,
					   xor_out=0x0000)
		
	def performCRC(self,data):
		return self.crc.bit_by_bit(data)

	def createPacket(self,doCRC=False):
		buffer = struct.pack("B",self.slaveAddy)
		buffer += struct.pack("B",self.functionCode)
		if doCRC:
			buffer += struct.pack("<H",self.performCRC(buffer))
		return buffer

	def processReply(self,rplyBuf):
		startPos = rplyBuf.tell()
		if len(rplyBuf.getvalue()) == 0:
				raise serialComm.EmptyRplyError(self,rplyBuf.getvalue())
		rplySlaveAddy = rplyBuf.read(1)
		self.rplyFunctionCode = struct.unpack("B",rplyBuf.read(1))[0]
		if self.rplyFunctionCode != self.functionCode:
			rplyBuf.seek(startPos)
			raise FujiPXR4RplyFuncErorr(self,rplyBuf.getvalue())

	def __str__(self):
			return "slave addy: " + str(self.slaveAddy) + "\n" + "function code: " + str(self.functionCode) + "\n" + "rplyFunctionCode: " + str(self.rplyFunctionCode) + "\n" + "crc: " + str(self.crc)

class FujiPXR4ReadWordCmd(FujiPXR4Cmd):
	"""blah blah blah"""
	def __init__(self,slaveAddy,startAddy,dataQty,cmdCode):
		FujiPXR4Cmd.__init__(self,slaveAddy,cmdCode)
		self.startAddy = startAddy
		self.dataQty = dataQty
		self.rplyDataQty = -1
		self.rplyVal = list()

	def createPacket(self,doCRC=False):
		buffer = FujiPXR4Cmd.createPacket(self)
		buffer += struct.pack("BB",self.startAddy[0],self.startAddy[1])
		buffer += struct.pack(">H",self.dataQty)
		if doCRC:
			buffer += struct.pack("<H",self.performCRC(buffer))
		return buffer

	def processReply(self,rplyBuf):
		FujiPXR4Cmd.processReply(self,rplyBuf)
		self.rplyDataQty = ord(rplyBuf.read(1))/int(2) # number of words
		# TODO: check rplyDataQty
		for i in range(self.rplyDataQty):
			self.rplyVal.append(struct.unpack(">H",rplyBuf.read(2))[0])

class FujiPXR4ReadSVCmd(FujiPXR4ReadWordCmd):
	""" blah blah blah"""
	def __init__(self,slaveAddy,sensorID):
		FujiPXR4ReadWordCmd.__init__(self,slaveAddy,(0x03,0xEA),1,0x03)
		self.sensorID = sensorID
	def getSV(self):
		if self.rplyVal:
			return self.rplyVal[0]/10.
		else:
			return None
	def toWWWparam(self):
		# TODO: process raw data to eng units
		return (str(self.sensorID),
				str(self.getSV()))
	def to_JSON_WWW_data(self,readingTime):
		return [{"sensor_id":self.sensorID,
				 "type":"SP",
				 "value":self.getSV(),
				 "raw_data":self.getSV(),
				 "datetime":readingTime.isoformat()}]
	def __str__(self):
		return FujiPXR4Cmd.__str__(self) + "\nsensor ID: "+str(self.sensorID)+"\nSV: "+str(self.getSV())

class FujiPXR4ReadRunCmd(FujiPXR4ReadWordCmd):
	"""blah blah blah"""
	def __init__(self,slaveAddy):
		FujiPXR4ReadWordCmd(slaveAddy,(0x03,0xEB),1,0x03)

class FujiPXR4ReadPVCmd(FujiPXR4ReadWordCmd):
		"""blah blah blah"""
		def __init__(self,slaveAddy,sensorID):
				FujiPXR4ReadWordCmd.__init__(self,slaveAddy,
											 (0x03,0xE8),1,0x04)
				self.sensorID=sensorID
		def getPV(self):
			return self.rplyVal[0]/10.
		def toWWWparam(self):
				# TODO: process raw data to eng units
				return (str(self.sensorID),str(self.getPV()))
		def to_JSON_WWW_data(self,readingTime):
			return [{"sensor_id":self.sensorID,
					 "type":"PV",
					 "value":self.getPV(),
					 "raw_data":self.getPV(),
					 "datetime":readingTime.isoformat()}]
		def __str__(self):
				return FujiPXR4ReadWordCmd.__str__(self)+"\nPV:"+str(self.getPV())


class  FujiPXR4WriteWordCmd(FujiPXR4Cmd,EA_RCcmd):
	"""blah blah blah"""
	CMD_CODE = 0x06
	def __init__(self,slaveAddy,addy,ctl_id,value):
		FujiPXR4Cmd.__init__(self,slaveAddy,self.CMD_CODE)
		EA_RCcmd.__init__(self,ctl_id)
		self.addy = addy
		self.value = value
		self.rplyAddy = 0
		self.rplyValue = 0
	def createPacket(self,doCRC=False):
		buffer = FujiPXR4Cmd.createPacket(self)
		buffer += struct.pack("BB",self.addy[0],self.addy[1])
		buffer += struct.pack(">H",self.value)
		if doCRC:
			buffer += struct.pack("<H",self.performCRC(buffer))
		return buffer

	def processReply(self,rplyBuf):
		FujiPXR4Cmd.processReply(self,rplyBuf)
		self.rplyAddy = struct.unpack("BB",rplyBuf.read(2))
		self.rplyValue = struct.unpack(">H",rplyBuf.read(2))[0]
		if self.rplyValue != self.value:
				raise FujiPXR4RplyValueError(self)
		# self.rplyCRC = struct.unpack(">H",rplyBuf.read(2))

class FujiPXR4SetSVCmd(FujiPXR4WriteWordCmd):
	"""blah blah blah"""
	ADDY = (0x03,0xEA)
	def __init__(self,slaveAddy,ctl_id,value):
		FujiPXR4WriteWordCmd.__init__(self,slaveAddy,self.ADDY,ctl_id,int(math.floor(value*10.)))

	def __str__(self):
		return FujiPXR4Cmd.__str__(self)+"\nMem addy:"+str(self.addy)+"\nNew value:"+str(self.value)+"\nRply addy:"+str(self.rplyAddy)+"\nRply value:"+str(self.rplyValue)

class FujiPXR4OnCmd(FujiPXR4WriteWordCmd):
	"""blah blah blah"""
	ADDY = (0x03,0xEB)
	VALUE = 0
	def __init__(self,slaveAddy):
		FujiPXR4WriteWordCmd.__init__(self,slaveAddy,self.ADDY,self.VALUE)

class FujiPXR4StandbyCmd(FujiPXR4WriteWordCmd):
	"""blah blah blah"""
	ADDY = (0x03,0xEB)
	VALUE = 1
	def __init__(self,slaveAddy):
		FujiPXR4WriteWordCmd.__init__(self,slaveAddy,self.ADDY,self.VALUE)


class FujiPXR4RplyFuncErorr(EAMIDexception):
		def __init__(self,cmd,rply):
				self.cmd=cmd
				self.rply=rply

class FujiPXR4WriteError(EAMIDexception):
		def __init__(self,cmd):
				self.cmd = cmd


if __name__ == "__main__":
	port = sys.argv[1]
	slaveAddr = int(sys.argv[2])
	newSP = int(sys.argv[3])
	# setup serial communication
	sc = serialComm.SerialComm("/dev/ttyUSB0")
	# create and process a read SP command
	readSPcmd = FujiPXR4ReadSVCmd(slaveAddr,0)
	sc.processCommand(readSPcmd)
	print readSPcmd
	# create and process a read PV command
	readPVcmd = FujiPXR4ReadPVCmd(slaveAddr,0)
	# create and process a write SP command
	setSPcmd = FujiPXR4SetSVCmd(slaveAddr,0,newSP)

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
