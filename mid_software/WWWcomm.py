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
# std lib
import datetime
import json
import logging
# restkit
from restkit import Resource
import requests
# EA mods
from EAMIDexception import EAMIDexception

class WWWcomm:

	def __init__(self,MIDpass,configPath,baseURL,uploadPath,RCstatusPath,MIDname=None):
		# self.baseURL = defaultConfig.baseURL
		# self.password = defaultConfig

		# obtain base configuration
		self.MIDpass = MIDpass
		self.baseURL = baseURL
		self.configPath = configPath
		self.resource = Resource(baseURL,timeout=60)
		# self.upResource = Resource("http://isadoredev1.exotericanalytics.com:5050")
		self.uploadPath = uploadPath
		self.RCstatusPath = RCstatusPath
		self.MIDname = MIDname

	def getConfig(self):
		params_dict = {"mid_pass":self.MIDpass,"ts":"blah"}
		if self.MIDname:
			params_dict["mid_name"]=self.MIDname
		output = self.resource.get(path=self.configPath, 
								   params_dict=params_dict,
								   verify=False)
		
		logging.debug("WWW reply status code: "+str(output.status_int)+".")
		if output.status_int != 200:
			raise MIDconfigDownloadError(output)

		return json.loads(output.body_string())

	def RC_cmd_status(self,control_id,fetched_p):
			"""
			"""
			# TODO: check output for errors, don't just rely upon exceptions
			try:
					if fetched_p:
							output = self.resource.put(path=self.RCstatusPath+str(control_id),
													   params_dict={"fetched":1,
																	"MID_pass":self.MIDpass},
													   verify=False)
					else:
							output = self.resource.put(path=self.RCstatusPath+str(control_id),
													   params_dict={"fetched":0,
																	"MID_pass":self.MIDpass},
													   verify=False)
					if output.status_int != 204:
							raise MID_RCstatusError("Failed to inform WWW of successful RC command: " + str(control_id) + ".  Received response status int: " + str(output.status_int))
			except Exception as e:
					raise MID_RCstatusError("Failed to inform WWW of unsuccessful RC command: " + str(control_id) + ".  This is the result of exception: " + str(e))

	def uploadData(self,paramString):
		# output = self.upResource.get(path=self.uploadPath,
		# 							 params_dict={"data":paramString})
		# NOTE: can remove verify param once we upgrade Python to 2.7.9+
		output = self.resource.post(path=self.uploadPath,
									params_dict={"data":paramString},
									verify=False)
		output.skip_body()		# to release the connection
		return output

	def uploadReading(self,passwd,readingTime,cmds,errors):
		payload =  {"mid_pass":passwd, 
					"datetime":readingTime.isoformat(),
					"data":json.dumps(reduce(lambda x,y: x+y.to_JSON_WWW_data(readingTime), cmds, [])),
					"errors":[]}
		# TODO: deal with requests-specific exceptions. in particular, the timeout exception.  for now, letting MID.py deal with it.
		# NOTE: can remove verify param once we upgrade Python to 2.7.9+
		logging.debug(payload["data"])
		r = requests.post(self.baseURL+self.uploadPath,data=payload,timeout=60.0,verify=False)
		# TODO: inspect reply
		

def buildJSONupload(passwd,readingTime,cmds,errors):
	return json.dumps({"passwd":passwd, 
					   "datetime":readingTime.isoformat(),
					   "data":reduce(lambda x,y: x+y.to_JSON_WWW_data(readingTime), cmds, []),
					   "errors":[]},
					  sort_keys=True,
					  separators=(',',':'))

class MID_WWW_commError(EAMIDexception):
	def __init__(self,WWWoutput):
		self.WWWoutput = WWWoutput

class MIDconfigDownloadError(MID_WWW_commError):
	"""
	"""

class MIDuploadError(MID_WWW_commError):
	"""
	"""

class MID_RCstatusError(MID_WWW_commError):
	"""
	"""
	def __init__(self,msg):
			self.msg = msg

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
