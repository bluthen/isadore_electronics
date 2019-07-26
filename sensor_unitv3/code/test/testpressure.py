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
import sys
from crc_algorithms import Crc

def maxim_ibutton_crc(data):
	crc = Crc(width=8, poly=0x31, reflect_in = True, xor_in=0x00, reflect_out = True, xor_out=0x00)
	return crc.bit_by_bit(data)

ser = serial.Serial("/dev/ttyS0", 9600, timeout=5)
print "Opened: "+ser.portstr
address=int(sys.argv[1])
print "Trying address: "+str(address)

send_buffer = struct.pack("<4sHB", "DERV", address, 7)
print str(len(send_buffer))+", "+send_buffer
ser.write(send_buffer)
d=ser.read(11)
print "recv len: "+str(len(d))
#XXX: Check address and CRC
magic = "".join(d[0:4])
address = struct.unpack("<H", d[4:6])[0]
cc = struct.unpack("B", d[6])
s= struct.unpack("B", d[7])
pressure=struct.unpack("<H", d[8:10])[0]
crc = struct.unpack("B", d[10])[0]
print "MAGIC: "+magic
print "ADDRESS: "+str(address)
print "CC: "+str(cc)
print "S: "+str(s)
print "RAW p: "+str(pressure)
print "CRC: "+str(crc)
recalc_crc = maxim_ibutton_crc("".join(d[0:10]))
print "Re-CRC: "+str(recalc_crc)

pressure = 0.0022888*pressure+50.0
print "Pressure: "+str(pressure)
