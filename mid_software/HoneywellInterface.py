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
from crc_algorithms import Crc

# TODO: fold some of this into a general MODBUS class
# TODO: add CRC check when processing replies

class Honeywell3300ReadRegisterCmd:
	"""Only class in this interface thus far.  We are only reading from these units."""
	def __init__(self,slaveAddy,functionCode,registerAddy,numRegisters):
		self.slaveAddy = slaveAddy
		self.functionCode = functionCode
		self.registerAddy = registerAddy
		self.numRegisters = numRegisters
		self.crc = Crc(width=16,poly=0x8005,reflect_in=True,
					   xor_in=0xFFFF,reflect_out=True,
					   xor_out=0x0000)
		self.rplyBytes = 0
		self.rplyData = list()	# list of 16 bit integer data

	def performCRC(self,data):
		return self.crc.bit_by_bit(data)

	def createPacket(self):
		buffer = struct.pack("B",self.slaveAddy)
		buffer += struct.pack("B",self.functionCode)
		buffer += struct.pack("BB",self.registerAddy[0],self.registerAddy[1])
		buffer += struct.pack(">H",self.numRegisters)
		buffer += struct.pack(">H",self.performCRC(buffer))
		return buffer

	def processReply(self,rplyBuf):
		startPos = rplyBuf.tell()
		
		rplySaveAddy = ord(rplyBuf.read(1))
		rplyFunctionCode = ord(rplyBuf.read(1))
		# TODO: addy and function code
		self.rplyBytes = ord(rplyBuf.read(1))
		# TODO: test length against expected length
		for i in range(len(self.numRegisters)):
			self.rplyData.append(int(struct.unpack(">H",rplyBuf.read(2))))

class Honeywell3300ReadSP_PVcmd(Honeywell3300ReadRegisterCmd):

	FUNCTION_CODE = 0x03
	REGISTER_ADDY = (0x00,0x00)
	NUM_REGISTERS = 2
	
	def __init__(self,slaveAddy,sensorIDs):
		Honeywell3300ReadRegisterCmd.__init__(slaveAddy,self.FUNCTION_CODE,self.REGISTER_ADDY,self.NUM_REGISTERS)
		self.sensorIDs = sensorIDs
	def getPV(self):
		return float(rplyData[0])/10.0
	def getSP(self):
		return float(rplyData[1])/10.0
	def toWWWParam(self):
		return (str(self.sensorIDs[0])+","+str(self.sensorIDs[1]),
			str(self.getPV())+ ","+str(self.getSV()))


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
