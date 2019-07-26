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
from tests import MIDWWWtests,MIDhubTests
import hubPackets
import hubComm
import cPickle

class createTestCmds (MIDWWWtests,MIDhubTests):
    """ blah """

    def setUp(self):
        self.simClassName = "demo1_simple"
        MIDhubTests.setUp(self)
        MIDWWWtests.setUp(self)

    def testCreateTestCmds(self):
        WWWcfg = self.WWWcon.getConfig()
	allCmds = []
	allCmds += hubComm.tempRHcmdsFromJSON(WWWcfg["commandInfo"])
	allCmds += hubComm.kpaCmdsFromJSON(WWWcfg["commandInfo"])
	allCmds += hubComm.TCcmdsFromJSON(WWWcfg["commandInfo"])
	allCmds += hubComm.tachCmdsFromJSON(WWWcfg["commandInfo"])
        allErrs = []
        for aC in allCmds:
            allErrs += [self.hubCon.processCommand(aC)]
        fh = open(self.config.get(self.simClassName,"saved_cmds_path"),"w")
        cPickle.dump(allCmds,fh)
        cPickle.dump(allErrs,fh)
        fh.close()

def loadTestCmds(filePath):
    fh = open(filePath,"r")
    allCmds = cPickle.load(fh)
    allErrs = cPickle.load(fh)
    fh.close()
    return allCmds,allErrs
    
