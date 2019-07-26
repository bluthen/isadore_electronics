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
import sys,time
import ConfigParser
import serialComm
import FujiInterface as fi

CONFIG_LOC = '../MID.cfg'

if __name__ == "__main__":
    slaveAddr = int(sys.argv[1])
    newSV = float(sys.argv[2])
    localConfig = ConfigParser.ConfigParser()
    localConfig.read(CONFIG_LOC)

    print "testing read PV cmd:\n========================"
    sc = serialComm.SerialComm(port=localConfig.get("MID","RS485_PORT"))
    readPVcmd = fi.FujiPXR4ReadPVCmd(slaveAddr,0)
    sc.processCommand(readPVcmd)
    sc.closeSer()
    print readPVcmd

    time.sleep(5)

    print "testing read SV cmd:\n====================="
    sc = serialComm.SerialComm(port=localConfig.get("MID","RS485_PORT"))
    readSVcmd = fi.FujiPXR4ReadSVCmd(slaveAddr,0)
    sc.processCommand(readSVcmd)
    sc.closeSer()
    print readSVcmd

    time.sleep(5)

    print "testing set SV cmd:\n====================="
    sc = serialComm.SerialComm(port=localConfig.get("MID","RS485_PORT"))
    readSVcmd = fi.FujiPXR4ReadSVCmd(slaveAddr,0)
    sc.processCommand(readSVcmd)
    sc.closeSer()
    print "pre:\n",readSVcmd
    sc = serialComm.SerialComm(port=localConfig.get("MID","RS485_PORT"))
    setSVcmd = fi.FujiPXR4SetSVCmd(slaveAddr,0,newSV)
    sc.processCommand(setSVcmd)
    sc.closeSer()
    print setSVcmd
    sc = serialComm.SerialComm(port=localConfig.get("MID","RS485_PORT"))
    readSVcmd = fi.FujiPXR4ReadSVCmd(slaveAddr,0)
    sc.processCommand(readSVcmd)
    sc.closeSer()
    print "post:\n",readSVcmd

    print "============== tested.... bitch! =================="
