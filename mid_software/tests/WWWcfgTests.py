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
from tests import MIDWWWtests
import hubComm

class WWWcfgTests (MIDWWWtests):
    """Tests for retreiving and parsing the WWW config info."""

    def testGetCfg(self):
        """Test ability to get latest WWW cfg."""
        WWWcfg = self.WWWcon.getConfig()
        # TODO: check something?

    def testParseCfg(self):
        """Somewhat superficially tests the ability to parse the downloaded MID cfg JSON"""
        # TODO: change this to load a stored cfg from a file that has all sensor types
        WWWcfg = self.WWWcon.getConfig()
        TRHcmds = hubComm.tempRHcmdsFromJSON(WWWcfg["commandInfo"])
	kpaCmds = hubComm.kpaCmdsFromJSON(WWWcfg["commandInfo"])
	TCcmds = hubComm.TCcmdsFromJSON(WWWcfg["commandInfo"])
	tachCmds = hubComm.tachCmdsFromJSON(WWWcfg["commandInfo"])
        self.assertEqual(len(TRHcmds),1,"incorrect number of T/RH cmds created: expected 1, found "+str(len(TRHcmds)))
        self.assertEqual(len(TRHcmds[0].sensorID),6,"Incorrect number of T/RH sensorIDs in one or more of the newly-created commands")
