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

send_buffer = struct.pack("<4sHB", "DERV", address, 1)
print str(len(send_buffer))+", "+send_buffer
ser.write(send_buffer)
d=ser.read(13)
print "recv len: "+str(len(d))
#XXX: Check address and CRC
magic = "".join(d[0:4])
address = struct.unpack("<H", d[4:6])[0]
cc = struct.unpack("B", d[6])
s= struct.unpack("B", d[7])
temp=struct.unpack("<H", d[8:10])[0]
hum = struct.unpack("<H", d[10:12])[0]
crc = struct.unpack("B", d[12])[0]
print "MAGIC: "+magic
print "ADDRESS: "+str(address)
print "CC: "+str(cc)
print "S: "+str(s)
print "RAW t,h: "+str(temp)+", "+str(hum)
print "CRC: "+str(crc)
recalc_crc = maxim_ibutton_crc("".join(d[0:12]))
print "Re-CRC: "+str(recalc_crc)
t=(-40.2)+0.018*temp
h=-2.0468+0.0367*hum+-1.5955e-6*hum**2
#h=-4.0+0.0405*hum-(2.8e-6 * hum**2)
h=(( (t-32.0)/1.8)-25)*(0.01+0.00008*hum)+h

print "Temp (F): "+str(t)
print "Humidity: "+str(h)
