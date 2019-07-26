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
# import pyserial
import serial
# import standard lib modules
import struct
import httplib
from types import NoneType

class VFDinterface():
	"""Base VFD class.  No meaningful functionality."""
	def __init__(self,sensorIDs):
		self.sensorIDs = sensorIDs # (Hz,feedback)
		self._Hz = 0
		self.HzScale = 10.0/60.0
		self._Amps = 0
		self.AmpsScale = 1.0
		self._RPMs = 0
		self.RPMsScale = 1.0
		self._RPMfeedback = 0
		self.RPMfeedbackScale = 1.0

	def getHz(self):
		return float(self._Hz)/self.HzScale

	def getAmps(self):
		return float(self._Amps)/self.AmpsScale

	def getRPMs(self):
		return float(self._RPMs)/self.RPMsScale

	def getRPMfeedback(self):
		return float(self._RPMfeedback)/self.RPMfeedbackScale

	def toWWWparam(self):
		return (str(self.sensorIDs[0]) + "," + str(self.sensorIDs[1]),
			str(self.getHz()) + "," + str(self.getRPMfeedback()))

	def to_JSON_WWW_data(self,readingTime):
		return [{"sensor_id":self.sensorIDs[0],
				 "type":"VFD Hz",
				 "value":self.getHz(),
				 "raw_data":self.getHz(),
				 "datetime":readingTime.isoformat()}]

	def __str__(self):
		""
		return "VFD info\n" + "=====================\n" + "Hz: " + str(self.getHz()) + "\nAmps: " + str(self.getAmps()) + "\nRPMs: " + str(self.getRPMs()) + "\nRPMfeedback: " + str(self.getRPMfeedback()) + "\n"

class YaskawaVFD(VFDinterface):
	""" blah blah blah"""
	def __init__(self,hostNum,sensorIDs):
		VFDinterface.__init__(self,sensorIDs)
		self.hostNum = hostNum

class YaskawaVFDcmd:
	"""blah blah blah"""
	def __init__(self,slaveAddy,functionCode):
		self.slaveAddy = slaveAddy
		self.functionCode = functionCode
		self.rplyFunctionCode = 0

	def createPacket(self):
		buffer = struct.pack("B",self.slaveAddy)
		buffer += struct.pack("B",self.functionCode)

	def processReply(self,rplyBuf):
		startPos = rplyBuf.tell()

		if len(rplyBuff.getvalue()) == 0:
			EmptyVFDRplyError(self,rplyBuf.getvalue())

		rplySlaveAddy = rplyBuf.read(1)
		
		self.rplyFunctionCode = rplyBuf.read(1)
		if self.rplyFunctionCode != self.functionCode:
			rplyBuf.seek(startPos)
			raise VFDRplyFuncErorr(self,rplyBuf.getvalue())

class YaskawaVFDReadRegisterCmd(YaskawaVFDcmd):

	READ_CODE = 0x02

	def __init__(self,slaveAddy,startAddy,dataQty):
		YaskawaVFDcmd.__init__(self,slaveAddy,self.READ_CODE)
		self.startAddy = startAddy
		self.dataQty = dataQty
		self.rplyDataQty = 0

	def createPacket(self):
		buffer = YaskawaVFDcmd.createPacket(self)
		buffer += struct.pack("BBBB",slaveAddy[0],slaveAddy[1],dataQty[0],dataQty[1])
		# compute CRC
		# buffer += struct.pack(YaskawaVFDcmd.computeCRC(buffer))

	def processReply(self,rplyBuf):
		YaskawaVFDcmd.processReply(self,rplyBuf)
		self.rplyDataQty = ord(rplyBuf.read(1))

		if self.rplyDataQty != 2 * self.dataQty:
			raise VFDRplySizeError(self,rplyBuf.getvalue())

class YaskawaVFDReadStatusCmd(YaskawaVFDReadRegisterCmd):

	OPERATION_MASK = 0x01
	DIRECTION_MASK = 0x02
	STARTUP_MASK = 0x04
	FAULT_MASK = 0x08

	FORWARD = 0
	REVERSE = 1
	
	def __init__(self,slaveAddy):
		YaskawaVFDReadRegisterCmd(slaveAddy,(0x00,0x20),(0x00,0x02))

		self.operating_p = None
		self.direction = None
		self.startupComplete_p = None
		self.fault_p = None

	def processReply(self,rplyBuf):
		YaskawaVFDReadRegisterCmd.processReply(self,rplyBuf)
		# get data we asked for
		registerData=struct.unpack("BBBB",rplyBuf.read(4))
		self.operating_p = registerData[0] & self.OPERATION_MASK
		self.direction = registerData[0] & self.DIRECTION_MASK
		self.startupComplete_p = registerData[0] & self.STARTUP_MASK
		self.fault_p = registerData[0] & self.FAULT_MASK
		# unpack and test CRC
		# TODO: grab fault descriptions

class YaskawaVFDReadFreqAndFriends(YaskawaVFDReadRegisterCmd):
	def __init__(self,slaveAddy):
		YaskawaVFDReadRegisterCmd(slaveAddy,(0x00,0x23),(0x00,0x05))

		self.freqRef = None
		self.outputFreq = None
		self.outputVoltage = None
		self.outputCurrent = None
		self.outputPower = None

	def processReply(self,rplyBuf):
		YaskawaVFDReadRegisterCmd.processReply(self,rplyBuf)
		# get data we asked for
		(self.freqRef,
		 self.outputFreq,
		 self.outputVoltage,
		 self.outputCurrent,
		 self.outputPower) = struct.unpack("<HHHHH",rplyBuf.read(10))
		# unpack and test CRC

class YaskawaVFDWriteCmd(YaskawaVFDcmd):
	WRITE_CODE = 0x06

	def __init__(self,slaveAddy,addy,value):
		YaskawaVFDcmd.__init__(self,slaveAddy,self.READ_CODE)
		self.addy = addy
		self.value = value
		self.rplyAddy = (0x00,0x00)
		self.rplyValue = 0

	def createPacket(self):
		buffer = YaskawaVFDcmd.createPacket(self)
		buffer += struct.pack("<BBH",self.addy[0],self.addy[1],self.value)
		# compute CRC
		# buffer += struct.pack(YaskawaVFDcmd.computeCRC(buffer))

	def processReply(self,rplyBuf):
		YaskawaVFDcmd.processReply(self,rplyBuf)
		# self.rplyDataQty = ord(rplyBuf.read(1))

		# if self.rplyDataQty != 2 * self.dataQty:
		# 	raise VFDRplySizeError(self,rplyBuf.getvalue())

		# grab the details of what the slave thinks we wanted to write
		(addy0,addy1,self.rplyValue) = struct.unpack("<BBH",rplyBuf.read(4))
		self.rplyAddy = (addy0,addy1)

		# TODO: check CRC
	
		
class YaskawaVFDWriteFreqRefCmd(YaskawaVFDWriteCmd):

	FREQ_REF_ADDY = (0x00,0x02)

	def __init__(self,value):
		YaskawaVFDWriteCmd.__init__(self,self.FREQ_REF_ADDY,value)

class AllenBradleyP70VFD(VFDinterface):
	""" Interface specific to Allen-Bradley P700 VFDs"""

	DEVICE_TYPE = 14
	LAN_PSEUDO_PORT = 0

	def __init__(self,IPaddy,sensorIDs,URL="diagnostics_5.html",HzTagName="Datalink A1 Out",AmpsTagName="Datalink A2 Out",RPMsTagName="Datalink A3 Out",RPMfeedbackTagName="Datalink A4 Out"):
		VFDinterface.__init__(self,sensorIDs)
		self.VFD_IP = IPaddy
		self.VFD_URL = URL
		self.HzTagName = HzTagName
		self.AmpsTagName = AmpsTagName
		self.RPMsTagName = RPMsTagName
		self.RPMfeedbackTagName = RPMfeedbackTagName

	def update(self):
		self.scrapeHTML()
	
	def getTDValue(self, doc, key):
		idx1=doc.find(key)
		if(idx1 < 0):
			return "0"
		idx2=doc.find('<td>', idx1)
		idx3=doc.find('</td>', idx2+4)
		return doc[idx2+4:idx3]

	def scrapeHTML(self):
		""" A-B sucks """
		# obtain HTML from VFD webpage
		httpC=httplib.HTTPConnection(self.VFD_IP)
		httpC.request("GET","/" + self.VFD_URL)
		httpR = httpC.getresponse()

		theDoc=httpR.read()
		self._Hz = int(self.getTDValue(theDoc, self.HzTagName))
		self._Amps = int(self.getTDValue(theDoc, self.AmpsTagName))
		self._RPMs = int(self.getTDValue(theDoc, self.RPMsTagName))
		self._RPMfeedback = int(self.getTDValue(theDoc, self.RPMfeedbackTagName))

def ABinterfaceFactory(config):
	"""returns a list of AB VFD interface class instances"""
	AB_VFDs = config["AB_VFD_special"]
	AB_VFDcmds = []
	for i in AB_VFDs:
		AB_VFDcmds.append(AllenBradleyP70VFD(i["name"],
											 tuple([int(j) for j in i["sensor_id"]])))
	return AB_VFDcmds


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
