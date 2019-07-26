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
import serial, struct, StringIO, json
from conversion import evalConversion

BOARD_NUMBERS = range(1,9)

def createCommands(JSON,serialPort,logging):
        RTM2000_json = filter(lambda x: x["type"]=="rtm2000",JSON)
        #
        # grab unique slave addresses
        #
        try:
                uniqueSlaveAddrs = list(set([json.loads(x["device_name"])["slaveAddr"] for x in RTM2000_json]))
        except Exception as e:
                logging.error("Problem when parsing JSON for a RTM2000 temperature point!")
                logging.error(str(e))
        #
        # for each slave addr and board number, grab all positions (keep in JSON)
        # make RTM2000Cmd objects
        # 
        RTM2000Cmds = []
        for slaveAddr in uniqueSlaveAddrs:
                for boardNum in BOARD_NUMBERS:
                        def testIncl(y,x):
                                jsonx = json.loads(x["device_name"])
                                if jsonx["slaveAddr"] == slaveAddr and jsonx["boardNum"] == boardNum:
                                        return y+[(x["sensor_id"],jsonx["position"])]
                                else:
                                        return y
                        sensorID_position_pairs = reduce(testIncl, RTM2000_json,[])
                        # make RTM2000Cmd objects
                        if sensorID_position_pairs:
                                RTM2000Cmds += [RTM2000Cmd([spp[0] for spp in sensorID_position_pairs],
                                                           slaveAddr,
                                                           boardNum,
                                                           [spp[1] for spp in sensorID_position_pairs],
                                                           serialPort,
                                                           logging)]
        return RTM2000Cmds

class RTM2000Cmd:
	def __init__(self, sensorIDs=None, slaveAddr=0, boardNum=2, positions=None, serialPort="/dev/ttyUSB0", logging=None):
	        self.sensorIDs = sensorIDs
		self.slaveAddr = slaveAddr
		self.boardNum = boardNum
                self.positions = positions
                self.serialPort = serialPort
                self.K_all = []
                self.F_all = []
		self.error = False
                self.logging = logging

        def _makeMODBUSCmd(self):
                buffer = struct.pack("B",ord("$"))
                buffer += struct.pack("B",self.slaveAddr)
                buffer += struct.pack("B",ord("t"))
                buffer += struct.pack("B",self.boardNum)
                buffer += struct.pack("B",0x66) # checksum is ignored b/c of DIP switch 6 setting
                buffer += struct.pack("B",ord("\r"))
                return buffer

        def _readMODBUSRply(self,ser):
                tmp_K_all = []
                rplyVal = []
                rplyBuf = StringIO.StringIO(ser.read(136))
                self.logging.info("data recieved from RTM2000 (or timed out)")
                asciiChr = rplyBuf.read(1)
                ret_id = struct.unpack("B",rplyBuf.read(1))
                ret_cmd = rplyBuf.read(1)
                board_id = struct.unpack("B",rplyBuf.read(1))
                self.logging.debug("Beginning info from RTM2000: "+asciiChr+","+str(ret_id)+","+str(ret_cmd)+","+str(board_id))
                self.logging.info("reading temperatures from RTM2000")
                for tempi in range(64+1):
                    K = struct.unpack("<H",rplyBuf.read(2))[0]
                    # C = float(K)/10.-273.2
                    # F = 1.8 * C + 32.
                    # self.logging.debug(str(tempi)+" "+str(K)+" "+str(C)+" "+str(F))
                    tmp_K_all += [K]
                CC = struct.unpack("B",rplyBuf.read(1))
                CR = struct.unpack("B",rplyBuf.read(1))
                self.logging.debug("end of response: "+str(CC)+" "+str(CR))
                self.logging.info("Finished reading RTM2000 temperatures")
                return (tmp_K_all)
                
	def _readTemps(self):
                ser = serial.Serial(port=self.serialPort,
                                    parity=serial.PARITY_NONE,
                                    baudrate=9600,
                                    stopbits=serial.STOPBITS_ONE,
                                    timeout=30)
                self.logging.debug("serial connection created")
                self.logging.debug(("%02x" % self.slaveAddr) + ("%02x" % self.boardNum))
                buffer = self._makeMODBUSCmd()
                ser.write(buffer)
                self.logging.info("command sent to RTM2000")
                try:
                        tmp_K_all = self._readMODBUSRply(ser)
                except Exception as e:
                        self.logging.error("Exception occured while reading from RTM2000: "+str(e))
                self.logging.info("copying values to object variables")
                self.K_all = []; self.F_all = [];
                for pos in self.positions:
                        K = tmp_K_all[pos]
                        C = float(K)/10.-273.2
                        F = 1.8 * C + 32.
                        self.K_all += [K]
                        self.F_all += [F]
                ser.close()

	def to_JSON_WWW_data(self, readingTime):
		return [{"sensor_id": sid,
			 "type": 'rtm2000',
			 "value": F,
			 "raw_data": K,
			 "datetime": readingTime.isoformat()} for (sid,F,K) in zip(self.sensorIDs,
                                                                                   self.F_all,
                                                                                   self.K_all)]
        def __str__(self):
                return "RTM2000 cmd\n==============\nslave addr: %i \nboard number: %i" % (self.slaveAddr,self.boardNum)+\
                        "\nsensorIDs: "+str(self.sensorIDs) +\
                        "\npositions: "+str(self.positions) +\
                        "\nraw: "+str(self.K_all)+\
                        "\neng: "+str(self.F_all)
