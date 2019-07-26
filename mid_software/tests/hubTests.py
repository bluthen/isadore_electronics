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
import unittest
import hubPackets
import hubComm

class hubTests(MIDhubTests):
	""" blah """
	def testHubConnect(self):
		"""Test ability to connect to Hub via EA ping packets"""
		pingCmd = hubPackets.HubPing(123)
		self.hubCon.processCommand(pingCmd)
		self.assertTrue(pingCmd.check(),"Pong value incorrect. Ping:"+str(pingCmd.pingVal)+" Pong:"+str(pingCmd.pongVal)+".")
	# def testMultipleUnits(self):
	# 	"""Test ability to collect measurements from multiple units"""
	# 	cmd = hubPackets.HubTempHumCmd(10,1,[404],convertPy=[("x","x")],bias=[(0,0)],binName="bin 1",binSectionName="section 1")

# class hubCommTests(MIDtests,MIDWWWtests):
#     """blah"""
#     def setUp(self):
#         MIDtests.setUp(self)
#         MIDWWWtests.setUp(self) 
#     def testBuildCommandsFromWWWcfg(self):
# 	cmdTally = [0,0,0,0]		# T/RH,wind,tach,pressure
# 	expectedTally = [2,1,0,1]
# 	WWWcfg = self.WWWcon.getConfig()
# 	cmdList = hubComm.buildAllCommands(WWWcfg)
# 	for c in cmdList:
# 	    cmdTally[0] += isinstance(c,hubPackets.HubTempHumCmd)
# 	    cmdTally[1] += isinstance(c,hubPackets.HubWindCmd)
# 	    cmdTally[2] += isinstance(c,hubPackets.HubTachCmd)
# 	    cmdTally[3] += isinstance(c,hubPackets.HubPressureCmd)
# 	for i,c in enumerate(zip(cmdTally,expectedTally)):
# 	    self.assertEqual(c[0],c[1],"Tally number "+str(i)+" not as expected.  "+str(c[0])+"!="+str(c[1])+".")
#         return cmdList
#     def testProcessCommandsFromWWWcfg(self):
#         cmdList = self.testBuildCommandsFromWWWcfg()
#         allErrs = [self.hubCon.processCommand(cmd) for cmd in cmdList]
#         self.assertEqual(reduce(lambda x,y: x or y,allErrs),None,"self.hubCon.processCommand returned one or more errors. "+str(allErrs))
#         return (cmdList,allErrs)
            
# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
