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
import serial
import StringIO

slvAddy = int(sys.argv[1])
boardNum = int(sys.argv[2])

crc = Crc(width=8,poly=0x8005,reflect_in=True,
	  xor_in=0xFFFF,reflect_out=True,
	  xor_out=0x0000)

# for slvAddy in range(63):
if True:
    # slvAddy = 0x01
    # boardNum = 0x08
    
    ser = serial.Serial(port="/dev/ttyUSB0",
                        parity=serial.PARITY_NONE,
                        baudrate=9600,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=30)
    # ser.open()
    print "poopy1"

    # # buffer = struct.pack("B",0x04)
    # print hex(slvAddy)
    # buffer = struct.pack("B",slvAddy)
    # buffer += struct.pack("B",0x03)
    # buffer += struct.pack("BB",0x01,0xF4)
    # buffer += struct.pack(">H",1)
    # buffer += struct.pack("<H",crc.bit_by_bit(buffer))
    # ser.write(buffer)

    print hex(slvAddy), hex(boardNum)
    buffer = struct.pack("B",ord("$"))
    buffer += struct.pack("B",slvAddy)
    buffer += struct.pack("B",ord("b"))
    buffer += struct.pack("B",boardNum)
    buffer += struct.pack("B",0x66) # checksum
    buffer += struct.pack("B",ord("\r"))
    ser.write(buffer)

    print "poopy2", buffer

    try:
        rplyVal = []
        rplyBuf = StringIO.StringIO(ser.read(136))
        print "read something"
        asciiChr = rplyBuf.read(1)
        ret_id = struct.unpack("B",rplyBuf.read(1))
        ret_cmd = rplyBuf.read(1)
        board_id = struct.unpack("B",rplyBuf.read(1))
        print asciiChr, ret_id, ret_cmd, board_id
        for Bi in range(64+1):
            B = struct.unpack("<B",rplyBuf.read(1))[0]
            print Bi,B
        CC = struct.unpack("B",rplyBuf.read(1))
        CR = struct.unpack("B",rplyBuf.read(1))
        print CC,CR,"somehow got all the way through this!"
    except Exception as e:
        print "poopy4", e
    # ser.close()
