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
# from isadore_web.server.src.tests import TestIsadore
import unittest
import ConfigParser
import MID
import hubComm
import subprocess
# import isadore_web.server.src.util as util

# TODO: do we need to do anything to clear out the pts before running a test or set of tests if a previous test failed?

MID_CONFIG_LOC = "/home/dane/EA/isadore_mid/python/tests/test.cfg"
# TODO: use these vars and the open/close mod-level functions below
CFG_SIM_SEC = "simulators"
CFG_SIM_PTS = "ptspath"
CFG_SIM_CWD = "cwd"
CFG_SIM_PY = "python"
CFG_SIM_SIM = "sim"

class MIDWWWtests (unittest.TestCase):
	""" For tests which require communication with a web server running the Isadore back-end software"""
	def setUp(self):
		# load configs
		self.config = ConfigParser.ConfigParser()
		self.config.read(MID_CONFIG_LOC)
		# create connection with web server
		self.WWWcon = MID.createWWWcon(self.config)

	def obtainWWWcfg(self):
		self.WWWcon.getConfig()

class MIDhubTests (unittest.TestCase):
	""" For tests which require communication with the hub."""
	def setUp(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read(MID_CONFIG_LOC)
		self.hubCon = hubComm.HubComm(serialPath=self.config.get("MID","hub_serial"))
		# start simulator
		self.startSimulator()
	def tearDown(self):
		# stop simulator
		self.stopSimulator()
		# do parent tearDown stuff
		unittest.TestCase.tearDown(self)
	def startSimulator(self):
		self.simProc = subprocess.Popen([self.config.get("simulators",
														 "python"),
										 self.config.get("simulators",
														 "sim"),
										 "-s",
										 self.config.get("simulators",
														 "ptspath"),
										 "-c",
										 self.config.get(self.simClassName,
														 "className")],
										cwd=self.config.get("simulators","cwd"))
	def stopSimulator(self):
		self.simProc.terminate()

class SimTests (unittest.TestCase):
	""" Remove once MIDHubTests is stable """
	def setUp(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read(MID_CONFIG_LOC)
		# start simulator
		self.startSimulator()
	def tearDown(self):
		# stop simulator
		self.stopSimulator()
		# do parent tearDown stuff
		unittest.TestCase.tearDown(self)
	def startSimulator(self):
		self.simProc = subprocess.Popen([self.config.get("simulators",
														 "python"),
										 self.config.get("simulators",
														 "sim"),
										 "-s",
										 self.config.get("simulators",
														 "ptspath"),
										 "-c",
										 self.config.get(self.simClassName,
														 "classname")],
										cwd=self.config.get("simulators","cwd"))

	def stopSimulator(self):
		self.simProc.terminate()


def startSimulator(pyPath,simFilename,ptsPath,simClassName,cwd):
	return subprocess.Popen([pyPath,simFilename,"-s",ptsPath,"-c",simClassName,cwd])

def stopSimulator(simProc):
		simProc.terminate()


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
