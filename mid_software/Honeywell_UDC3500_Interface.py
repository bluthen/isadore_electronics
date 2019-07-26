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
import math
from pymodbus.client.sync import ModbusTcpClient

class TCP_connection(object):
    """ Handles opening and closing connections to a UDC3500 """
    # TODO: add exceptions
    def __init__(self,slaveAddy):
        """ blah blah blah """
        """ param slaveAddy: a string representation of the UDC's IP address"""
        self.client = ModbusTcpClient(host=slaveAddy)
    def getClient(self):
        self.client.close()     # kinda a POS
        if not self.client.connect(): # make sure it can be re-opened
            # TODO: throw exception
            pass
        return self.client
    def __del__(self):
        self.client.close()     # kill it once and for all, i suppose

def getPV(conn):
    # TODO: add exception handling
    rsp = conn.getClient().read_holding_registers(0x0000,1)
    return rsp.getRegister(0) / 10.

def getSP(conn):
    # TODO: add exception handling
    rsp = conn.getClient().read_input_registers(0x0002,1)
    return rsp.getRegister(0) / 10.

def setSP(conn,newSP):
    # TODO: add exception handling
    intSP = int(math.floor(newSP * 10.))
    rsp = conn.getClient().write_register(0x0002,intSP)
    return True

def getOutput(conn):
    # TODO: add exception handling
    rsp = conn.getClient().read_input_registers(0x0003,1)
    return rsp.getRegister(0)/2.
