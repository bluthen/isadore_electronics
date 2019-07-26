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
from pymodbus.client.sync import ModbusTcpClient
import logging
import math

PV_ID = 20
SP_ID = 21
OUTPUT_ID = 22
HoneywellUDC2500_ID = 19
# HoneywellUDC3300_ID = 12
HoneywellUDC3500_ID = 16
DUMMY = 17

DEVICES = (HoneywellUDC2500_ID,
           HoneywellUDC3500_ID,
           DUMMY)
SENSORS = (PV_ID,SP_ID,OUTPUT_ID)

def check(deviceID,sensorTypeID):
    return (deviceID in DEVICES and sensorTypeID in SENSORS)

def factory(deviceID,sensorTypeID,sensorID,IPaddr,value=None):
    """ Return appropriate 3rd party device command instance.  If not the correct device type and sensor type, return an empty list."""
    if deviceID == HoneywellUDC3500_ID:
        if sensorTypeID == PV_ID:
            return Honeywell_UDC3500_getPV(sensorID,IPaddr)
        elif sensorTypeID == SP_ID:
            if value:
                return Honeywell_UDC3500_setSP(sensorID,IPaddr,value)
            else:
                return Honeywell_UDC3500_getSP(sensorID,IPaddr)
    elif deviceID == HoneywellUDC2500_ID:
        if sensorTypeID == PV_ID:
            return Honeywell_UDC2500_getPV(sensorID,IPaddr)
        elif sensorTypeID == SP_ID:
            if value:
                return Honeywell_UDC2500_setSP(sensorID,IPaddr,value)
            else:
                return Honeywell_UDC2500_getSP(sensorID,IPaddr)
    elif deviceID == DUMMY:
        if sensorTypeID == PV_ID:
            return Dummy_getPV(sensorID,IPaddr)
        elif sensorTypeID == SP_ID:
            if value:
                return Dummy_setSP(sensorID,IPaddr,value)
            else:
                return Dummy_getSP(sensorID,IPaddr)

class EthModbusCmd:
    def __init__(self, sensorID, IPaddr):
        self.sensorID=sensorID
        self.slaveAddr=IPaddr
        self.client = ModbusTcpClient(host=self.slaveAddr)
    def getClient(self):
        self.client.close()             # kinda a POS
        if not self.client.connect(): # make sure it can be re-opened
            # TODO: throw exception
            pass
        return self.client

    def execute(self):
        # doesn't do anything
        pass
    def to_JSON_WWW_data(self,readingTime):
        # TODO: not supposed to be here, throw an exception
        return []
    def __del__(self):
        self.client.close()

class Honeywell_UDC3500_getSP(EthModbusCmd):
    def __init__(self,sensorID,IPaddr):
        EthModbusCmd.__init__(self,sensorID,IPaddr)
        self.SP = None
    def execute(self):
        try:
            client = self.getClient()
            rsp = client.read_input_registers(0x0002,1)
            self.SP = rsp.getRegister(0) / 10.
            client.close()
        except Exception as e:
            logging.error("UDC3500 getSP failed: "+str(e))
    def to_JSON_WWW_data(self,readingTime):
        if self.SP:
            return [{"sensor_id":self.sensorID,
                     "type":"SP",
                     "value":self.SP,
                     "raw_data":self.SP,
                     "datetime":readingTime.isoformat()}]
        else:
            return []
    def shortDesc(self):
        return "UDC35000 get SP cmd, addr: "+self.slaveAddr

class Honeywell_UDC3500_getPV(EthModbusCmd):
    def __init__(self,sensorID,IPaddr):
        EthModbusCmd.__init__(self,sensorID,IPaddr)
        self.PV = None
    def execute(self):
        try:
            client = self.getClient()
            rsp = client.read_holding_registers(0x0000,1)
            self.PV = rsp.getRegister(0) / 10.
            client.close()
        except Exception as e:
            logging.error("UDC3500 getPV failed: "+str(e))
    def to_JSON_WWW_data(self,readingTime):
        if self.PV:
            return [{"sensor_id":self.sensorID,
                     "type":"PV",
                     "value":self.PV,
                     "raw_data":self.PV,
                     "datetime":readingTime.isoformat()}]
        else:
            return []
    def shortDesc(self):
        return "UDC35000 get PV cmd, addr: "+self.slaveAddr

class Honeywell_UDC3500_setSP(EthModbusCmd):
    def __init__(self,sensorID,IPaddr,value):
        EthModbusCmd.__init__(self,sensorID,IPaddr)
        self.newSP = value
    def execute(self):
        try:
            intSP = int(math.floor(self.newSP * 10.))
            client = self.getClient()
            rsp = client.write_register(0x0002,intSP)
            client.close()
        except Exception as e:
            logging.error("UDC3500 getSP failed: "+str(e))
    def to_JSON_WWW_data(self,readingTime):
        return []
    def shortDesc(self):
        return "UDC 3500 set SP cmd, addr: "+self.slaveAddr

class Honeywell_UDC2500_getSP(Honeywell_UDC3500_getSP):
    def __init__(self,sensorID,IPaddr):
        Honeywell_UDC3500_getSP.__init__(self,sensorID,IPaddr)
    def shortDesc(self):
        return "UDC2500 get SP cmd, addr: "+self.slaveAddr

class Honeywell_UDC2500_getPV(Honeywell_UDC3500_getPV):
    def __init__(self,sensorID,IPaddr):
        Honeywell_UDC3500_getPV.__init__(self,sensorID,IPaddr)
    def shortDesc(self):
        return "UDC2500 get PV cmd, addr: "+self.slaveAddr

class Honeywell_UDC2500_setSP(Honeywell_UDC3500_setSP):
    def __init__(self,sensorID,IPaddr,value):
        EthModbusCmd.__init__(self,sensorID,IPaddr)
        self.newSP = value
    def shortDesc(self):
        return "UDC2500 set SP cmd, addr: "+self.slaveAddr+", value: "+str(self.newSP)

class Dummy_getSP(EthModbusCmd):
    def __init__(self,sensorID,IPaddr):
        EthModbusCmd.__init__(self,sensorID,IPaddr)
        self.SP = None
    def execute(self):
        self.SP = 103.3
    def to_JSON_WWW_data(self,readingTime):
        return [{"sensor_id":self.sensorID,
                 "type":"SP",
                 "value":self.SP,
                 "raw_data":self.SP,
                 "datetime":readingTime.isoformat()}]

class Dummy_getPV(EthModbusCmd):
    def __init__(self,sensorID,IPaddr):
        EthModbusCmd.__init__(self,sensorID,IPaddr)
        self.PV = None
    def execute(self):
        self.PV = 102.8
    def to_JSON_WWW_data(self,readingTime):
        return [{"sensor_id":self.sensorID,
                 "type":"PV",
                 "value":self.PV,
                 "raw_data":self.PV,
                 "datetime":readingTime.isoformat()}]
