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
import createTestCmds
import WWWcomm
import cPickle
import datetime
import pytz

class uploadTests (MIDWWWtests):
    """Tests for uploading data to web server."""

    def setUp(self):
        self.simClassName = "demo1_simple"
        MIDWWWtests.setUp(self)

    def testUpload_nominalCase(self):
        """Tests uploading of data to web server using a pre-stored set of commands"""
        filePath = self.config.get(self.simClassName,"saved_cmds_path")
        allCmds,allErrs = createTestCmds.loadTestCmds(filePath)

        JSONuploadString = WWWcomm.buildJSONupload(")Frja62iB",datetime.datetime.now(pytz.utc),allCmds,allErrs)
        self.WWWcon.uploadData(JSONuploadString)
