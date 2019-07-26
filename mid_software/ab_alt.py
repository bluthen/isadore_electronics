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
import serial
import struct
import logging

import httplib
from types import NoneType

class VFDinterface():
	"""Base VFD class.  No meaningful functionality."""
	def __init__(self):
		self._Hz = 0
		self.HzScale = 1.0
		self._Amps = 0
		self.AmpsScale = 1.0
		self._RPMs = 0
		self.RPMsScale = 1.0
		self._RPMfeedback = 0
		self.RPMfeedbackScale = 1.0

	def getHz(self):
		return float(self._Hz)/self.HzScale

	def getAmps(self):
		return float(self._Amps)/self.AmpsScale

	def getRPMs(self):
		return float(self._RPMs)/self.RPMsScale

	def getRPMfeedback(self):
		return float(self._RPMfeedback)/self.RPMfeedbackScale



class AllenBradleyP70VFD(VFDinterface):
	""" Interface specific to Allen-Bradley P70 VFDs"""
	def __init__(self,IPaddy,URL,HzTagName="Datalink A1 Out",AmpsTagName="Datalink A2 Out",RPMsTagName="Datalink A3 Out",RPMfeedbackTagName="Datalink A4 Out"):
		VFDinterface.__init__(self)
		self.VFD_IP = IPaddy
		self.VFD_URL = URL
		# self.VFD_URL = "diagnostics_5.html"
		self.HzTagName = HzTagName
		self.AmpsTagName = AmpsTagName
		self.RPMsTagName = RPMsTagName
		self.RPMfeedbackTagName = RPMfeedbackTagName

	def update(self):
		self.scrapeHTML()
	
	def getTDValue(self, doc, key):
		idx1=doc.find(key)
		if(idx1 < 0):
			return "0"
		idx2=doc.find('<td>', idx1)
		idx3=doc.find('</td>', idx2+4)
		return doc[idx2+4:idx3]

	def scrapeHTML(self):
		""" A-B sucks """
		# obtain HTML from VFD webpage
		httpC=httplib.HTTPConnection(self.VFD_IP)
		httpC.request("GET","/" + self.VFD_URL)
		httpR = httpC.getresponse()

		#test
		#httpR = open('diagnostics_5.html', 'r')
		theDoc=httpR.read()
		self._Hz = int(self.getTDValue(theDoc, self.HzTagName))
		self._Amps = int(self.getTDValue(theDoc, self.AmpsTagName))
		self._RPMs = int(self.getTDValue(theDoc, self.RPMsTagName))
		self._RPMfeedback = int(self.getTDValue(theDoc, self.RPMfeedbackTagName))
		logging.debug("finished")
		logging.debug(self._Hz)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
