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
from tests import MIDhubTests
import hubPackets
import hubComm
from EAMIDexception import EAMIDexception

class sensorTests (MIDhubTests):
    """ blah """

    def setUp(self):
        self.simClassName = "sensorTests"
        MIDhubTests.setUp(self)

    def testTempHum(self):
        """Test ability to get a single temp/hum value."""
        try:
            cmd = hubPackets.HubTempHumCmd([(10,10)],1,[1007],convertPy=[("x","x")],bias=[(0,0)],binName="bin 1",binSectionName="section 1")
            errors = self.hubCon.processCommand(cmd)
        except EAMIDexception as e:
            self.assertTrue(False,"An exception has occurred: "+str(e))
        self.assertTrue(errors.isEmpty_p(),"Errors detected during processing of temp/hum cmd: "+str(errors))

    def testPressureWide(self):
        """Test ability to get a single pressure wide value."""
        try:
            cmd = hubPackets.HubPressureWideCmd([10,10,10],1,[1005,1004,1006],convertPy=["x","x","x"],bias=[0,0,0],binName="bin 3",binSectionName="section 2")
            errors = self.hubCon.processCommand(cmd)
        except EAMIDexception as e:
            self.assertTrue(False,"An exception has occurred: "+str(e))
        self.assertTrue(errors.isEmpty_p(),"Errors detected during processing of pressure cmd: "+str(errors))
        print cmd

    def testTach(self):
        """Test ability to get a single tachometer wide value."""
        try:
            cmd = hubPackets.HubTachCmd([10],1,[2000],convertPy=["x"],bias=[0],binName="NW burner house",binSectionName="fan")
            errors = self.hubCon.processCommand(cmd)
        except EAMIDexception as e:
            self.assertTrue(False,"An exception has occurred: "+str(e))
        self.assertTrue(errors.isEmpty_p(),"Errors detected during processing of tach cmd: "+str(errors))

    def testErrorCode4(self):
        """Test ability to parse error value among good values."""
        tstAddys = [1007,1008,1012,1009,1010,1011]
        try:
            cmd = hubPackets.HubTempHumCmd([10]*len(tstAddys),1,tstAddys,
                                           convertPy=[("x","x"),("x","x"),("x","x"),("x","x"),("x","x"),("x","x")],
                                           bias=[(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)],binName="bin 1",binSectionName="section 1")
            errors = self.hubCon.processCommand(cmd)
        except EAMIDexception as e:
            # self.assertTrue(False,"Exception ocurred: "+str(e))
            raise(e)
        self.assertFalse(errors.isEmpty_p(),"Errors not detected during processing commands (but should have been).")

    def testBadCCReply(self):
        """ Test ability to deal with a bad CC reply code."""
        cmd = hubPackets.HubTempHumCmd([(10,10)],1,[1301],
                                       convertPy=[("x","x")],bias=[(0,0)],
                                       binName="bin 1",binSectionName="section 1")
        errors = self.hubCon.processCommand(cmd)
        # TODO: should test the types of errors as well, but this will do for now, I think
        self.assertFalse(errors.isEmpty_p(),"errors expected but not returned.")
            
