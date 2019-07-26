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
import FujiInterface
# from HoneywellInterface import Honeywell3300ReadSP_PVcmd
import VFDinterface
import StringIO
from EAMIDexception import EAMIDexception

FujiPXR4_ID = 11
FujiPXR4_PV_ID = 20
FujiPXR4_SV_ID = 21

HoneywellUDC3300_ID = 12
HoneywellUDC3300_PV_ID = 16
HoneywellUDC3300_SP_ID = 17

YaskawaP7_ID = 15
YaskawaP7_RPM_ID = 60
YaskawaP7_Amps_ID = 61

RS485DeviceIDs = (FujiPXR4_ID,HoneywellUDC3300_ID,YaskawaP7_ID)

def isRS485_p(deviceID):
	return deviceID in RS485DeviceIDs
	
def cmdFactory(deviceID,sensorTypeID,sensorID,addy,value=None):
	if deviceID == FujiPXR4_ID:
		if sensorTypeID == FujiPXR4_PV_ID:
			return FujiInterface.FujiPXR4ReadPVCmd(addy,sensorID=sensorID)
		elif sensorTypeID == FujiPXR4_SV_ID:
			if value:
				return FujiInterface.FujiPXR4SetSVCmd(addy,
													  sensorID, # sensorID is ctl_id
													  value)
			else:
				return FujiInterface.FujiPXR4ReadSVCmd(addy,sensorID=sensorID)
	# elif deviceTypeID == Honeywelludc3300_Id:
	#	  return Honeywell3300ReadSP_PVcmd(*args,sensorID)
	elif deviceID == YaskawaP7_ID:
		pass
	else:
		pass

class SerialComm:
	"""blah blah blah"""
	def __init__(self,port="/dev/ttyUSB1"):
		self.port = port
		self.ser = serial.Serial(port=port,parity=serial.PARITY_ODD,
								 baudrate=9600,timeout=5)
	def processCommand(self,cmd):
		# send command
		sndBuf = cmd.createPacket(True)
		self.ser.write(sndBuf)
		# receive reply
		rplyBuf = StringIO.StringIO(self.ser.read(100))
		# parse reply
		cmd.processReply(rplyBuf)

	def closeSer(self):
		self.ser.close()

class EmptyRplyError(EAMIDexception):
	def __init__(self,cmd,rply):
		self.cmd=cmd
		self.rply=rply
# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
