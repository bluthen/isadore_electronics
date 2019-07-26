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
import unittest
from tests import MIDhubTests
import hubComm
import hubPackets

class hubCommTests(unittest.TestCase):
    
    def testCreatePressureSuperSampleCmds(self):
        tstCmds = hubComm.kpaCmdsFromJSON([{"type":"pressure",
                                            "port":1,
                                            "sensor_id":100,
                                            "addy":100,
                                            "convert":"x",
                                            "bias":0}])
        self.assertEqual(len(tstCmds),hubPackets.PRESSURE_SAMPLES_PER_READING+1) # +1 b/c of the super sample cmd itself
        
    def testPressureToJSONWWW(self):
        """simple test to make sure only super sampling pressure wide class generates JSON for WWWW"""
        tstCmds = hubComm.kpaCmdsFromJSON([{"type":"pressure","port":1,"sensor_id":100,"addy":100,"convert":"x","bias":0},
                                           {"type":"pressure","port":1,"sensor_id":101,"addy":102,"convert":"x","bias":0},
                                           {"type":"pressure","port":2,"sensor_id":102,"addy":103,"convert":"x","bias":0},
                                           {"type":"pressure","port":2,"sensor_id":103,"addy":104,"convert":"x","bias":0}])       
        # make sure correct number of commands
        self.assertEqual(len(tstCmds),2*hubPackets.PRESSURE_SAMPLES_PER_READING+1) # +1 b/c of the super sample cmd itself
        # throw some raw and eng data in there
        for tci,tc in enumerate(tstCmds[:-1]):
            tc.raw += [tci+10.]*2; tc.eng += [float(tci)]*2;
        tstJSON = reduce(lambda x,y: x+y.to_JSON_WWW_data(), tstCmds, [])
        self.assertEqual(len(tstJSON),4) # only super class should return a JSON item

    
