from tests import MIDhubTests
import unittest
import hubPackets
import hubComm

class simTests(MIDhubTests):
	""" Change to us MIDHubTests once it is stable and working """
	def setUp(self):
		self.simClassName = "simtests"
		MIDhubTests.setUp(self)
	def testSimStart(self):
		"""Test ability to start and stop a simulator, this test does nothing - all functionality handled by parent test class"""
		pass

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
