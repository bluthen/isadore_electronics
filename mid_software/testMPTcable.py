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
import hubComm
import hubPackets
import sys

if __name__ == "__main__":
    hubCon = hubComm.HubComm(serialPath="/dev/ttyAMA0")
    port = int(raw_input("port #: "))
    channel = int(raw_input("channel #: "))
    address = int(raw_input("address: "))
    addressList = []
    # get addresses until we get the NULL address
    print "getting addresses..."
    tmpAddressList = []
    resetCmd = hubPackets.MultiTResetCmd(port,[address])
    hubCon.processCommand(resetCmd)
    while True:
        addrCmd = hubPackets.MultiTAddrCmd(0,channel,port,[address])
        hubCon.processCommand(addrCmd)
        if addrCmd.addrs[0] == 18446744073709551615L:
            break
        tmpAddressList += [addrCmd.addrs[0]]
    print "done.  Detected ",str(len(tmpAddressList))," addresses."
    print "Testing temperatures..."
    resetCmd = hubPackets.MultiTResetCmd(port,[address])
    hubCon.processCommand(resetCmd)
    for addr in tmpAddressList:
        tempCmd = hubPackets.MultiTcmd(0,channel,port,[address])
        hubCon.processCommand(tempCmd)
        print str(addr)," : ",str(tempCmd.eng[0])
    print "done."
    print "BYE!!!!"
