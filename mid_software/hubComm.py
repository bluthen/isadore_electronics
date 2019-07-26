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
import socket
import StringIO
import serial
import struct
import logging
import traceback
# EA modules
import hubPackets
import json
from hubPackets import HubTachCmd,HubTempHumCmd,HubTachCmd,HubTCCmd,HubPressureWideCmd,HubPressureWideSuperCmd, MultiTSuperCmd, HubWindCmd
from EAMIDexception import EAMIDexception

MAX_NUM_PHYSICAL_PORTS = 6
MAX_NUM_MULTI_PT_CHANNELS = 4

"""
kjdfkjd
"""

class HubComm:
		"""
		djfdkj
		"""
		def __init__(self,localIP=None,localPortNum=None,hubIP=None,hubPortNum=None,socketTimeout=45,serialPath=None):
				self.serialDevice=None
				if(serialPath):
					# TODO: why wasn't 5*32 working?
					self.serialDevice = serial.Serial(serialPath, 9600, timeout=10*32)
				else:
					self.MIDaddy = (localIP,localPortNum)
					self.hubAddy = (hubIP,hubPortNum)
	
					# EA RS485 connections
					self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
					# configure udp connection
					self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					self.udp.bind(self.MIDaddy)
					self.udp.setblocking(1)
					self.udp.settimeout(socketTimeout)

		def clearUDP(self):
				"""Clear UDP recv buffer """
				try:
						self.udp.setblocking(0)
						while(len(self.udp.recv(512)) != 0):
								pass
						self.udp.setblocking(1)
				except:
						pass

		def clearSerial(self):
			self.serialDevice.flushInput()
			self.serialDevice.flushOutput()

		def clearComm(self):
			if self.serialDevice:
				self.clearSerial()
			else:
				self.clearUDP()

		def processCommand(self,cmd):
				# one object to hold all errors (should only use once anyway, me thinks)
				errorResp = hubPackets.HubErrorResponse()
				# create string to send to hub
				pktData = cmd.createPacket()
				# 
				# if packet created, process it
				# otherwise, just quit
				# 
				if pktData:
					# send command
					if(self.serialDevice):
						self.clearSerial()
						self.serialDevice.write(pktData)
					else:
						self.udp.sendto(pktData,self.hubAddy)
					# receive command
					try:
						if(self.serialDevice):
							# TODO: stop throwing CC away and use it
							l=struct.unpack("<H", self.serialDevice.read(2))[0]
							rplyData = self.serialDevice.read(l-2)
						else:
							rplyData = self.udp.recv(512)
					except (socket.timeout, serial.SerialTimeoutException):
						raise hubPackets.HubTimeoutError(cmd)
					if len(rplyData) == 0:
							raise hubPackets.HubRplyEmptyError()
					logging.debug("Length of reply data: " + str(len(rplyData)))
					rplyBuf = StringIO.StringIO(rplyData)
					#
					# parse command and error responses until we can't process no more
					#
					while True:
						try:
							# attempt to parse the buffer using the given command obj
							# logging.debug("attempting to process buffer as cmd: " + str(cmd))
							cmd.processReply(rplyBuf)
						except hubPackets.HubRplyCmdError:
							# unable to parse buffer using the given command obj
							# this is, hopefully, an error response, attempt to parse as an error
							try:
								logging.info("failed to process buffer as cmd, trying to process as an error response")
								errorResp.processReply(rplyBuf)
							except hubPackets.NotHubErrorCodeError:
								# this is unexpected, we are unable to parse the buffer any longer
								# raise an exception and exit
								logging.error("Unable to parse rplyBuf as a command or as an error response.  Am giving up.")
								raise BadHubReplyError()
						except hubPackets.HubRplyEngValueError as e:
							# add to errorResp the indices of the offending indices
							errorResp.addEngValErrors(e.idxs)
							# TODO: log this event
						except (hubPackets.HubRplyFatalError) as e:
							# these are the exceptions which try MIDs' souls: just give up
							# mark all readings as invalid
							errorResp.addParseErrors(e.theCmd.getSensorIDs())
							# rply buf read pos past packet data
							hubPackets.passPacket(e.rplyData,e.startPos,e.packetSize)
							# TODO: log this event
						except hubPackets.EmptyHubRplyError:
							# reached the end of the reply, exit the loop
							break
				return errorResp

def allCmdsFromJSON(JSON):
	allCmds = []
	logging.debug("start of command creation from JSON")
	allCmds += tempRHcmdsFromJSON(JSON["commandInfo"])
	logging.debug("created all T/RH cmds")
	allCmds += kpaCmdsFromJSON(JSON["commandInfo"])
	logging.debug("created all KPA cmds")
	allCmds += TCcmdsFromJSON(JSON["commandInfo"])
	logging.debug("created all TC cmds")
	allCmds += tachCmdsFromJSON(JSON["commandInfo"])
	logging.debug("created all tach cmds")
	allCmds += anemometerCmdsFromJSON(JSON["commandInfo"])
	logging.debug("created all wind cmds")
	try:
		allCmds += multiPtCmdsFromJSON(JSON["commandInfo"])
	except Exception as e:
		logging.debug("Error while creating MPT cmds: " + str(e))
		logging.debug(traceback.format_exc())
	logging.debug("created all MPT cmds")
	return allCmds

def tempRHcmdsFromJSON(JSON):
	# TODO: exception handling!
	# TODO: limit to 32 addresses per command!
	cmds = []
	for port in range(1,MAX_NUM_PHYSICAL_PORTS+1):
		t_rh_json = filter(lambda x: x["type"]=="temp_rh" and x["port"]==port,JSON)
		if t_rh_json:
			json_grps = limitTo32(t_rh_json)
			for json_grp in json_grps:
				# TODO: what to do with bin and bin_section names?
				cmds += [HubTempHumCmd(sensorID=[(trh["temp_id"],trh["rh_id"]) for trh in json_grp],
									   port=port,
									   addy=[(trh["addy"]) for trh in json_grp],
									   convertPy=[(trh["temp_convert"],trh["rh_convert"]) for trh in json_grp],
									   bias=[(trh["temp_bias"],trh["rh_bias"]) for trh in json_grp])]
	return cmds

def kpaCmdsFromJSON(JSON):
	if filter(lambda x: x["type"]=="pressure", JSON):
		superCmd = HubPressureWideSuperCmd()
		return superCmd.createCmds(JSON) + [superCmd] # append super command b/c that is what is where we will get the JSON from
	else:
		return []

def anemometerCmdsFromJSON(JSON):
	cmds = []
	for port in range(1,MAX_NUM_PHYSICAL_PORTS+1):
		rel_json = filter(lambda x: x["type"]=="wind" and x["port"]==port,JSON)
		if rel_json:
			# TODO: what to do with bin and bin_section names?
			cmds += [HubWindCmd(sensorID=[trh["sensor_id"] for trh in rel_json],
								port=port,
								addy=[(trh["addy"]) for trh in rel_json],
								convertPy=[trh["convert"] for trh in rel_json],
								bias=[trh["bias"] for trh in rel_json])]
	return cmds

def tachCmdsFromJSON(JSON):
	cmds = []
	for port in range(1,MAX_NUM_PHYSICAL_PORTS+1):
		rel_json = filter(lambda x: x["type"]=="tach" and x["port"]==port,JSON)
		if rel_json:
			# TODO: what to do with bin and bin_section names?
			cmds += [HubTachCmd(sensorID=[trh["sensor_id"] for trh in rel_json],
								port=port,
								addy=[(trh["addy"]) for trh in rel_json],
								convertPy=[trh["convert"] for trh in rel_json],
								bias=[trh["bias"] for trh in rel_json])]
	return cmds

def multiPtCmdsFromJSON(JSON):
	# start by creating a list of all sensors noting their (port,sensorID,addr,ch,MPT addrs)
	cfg_sensors = []
	rel_json = filter(lambda x: x["type"]=="MP_T", JSON)
	for rj in rel_json:
		if json.loads(rj["sensor_extra_info"]):
			cfg_sensors += [(rj["port"],
							 rj["sensor_id"],
							 rj["addy"],
							 json.loads(rj["sensor_extra_info"])["ch"],
							 json.loads(rj["sensor_extra_info"])["addrs"])]
		else:
			logging.warning("WARNING: There is a MPT sensor with no sensor_extra_info")
			logging.debug(rj)
	logging.debug(cfg_sensors)
	# create a list of unique (port,addr,ch) tuples
	dev_tuples = list(set([(cs[0],cs[2],cs[3]) for cs in cfg_sensors]))
	# organize by (port,addr,ch) tuples
	sID_MPTaddr_list = []
	for dev_tuple in dev_tuples:
		# logging.debug("gathering MPTaddrs for "+str(dev_tuple))
		sID_MPTaddr_list += [[[],[]]]
		for cs in cfg_sensors:
			if dev_tuple[0] == cs[0] and dev_tuple[1] == cs[2] and dev_tuple[2] == cs[3]:
				sID_MPTaddr_list[-1][0] += [cs[1]]
				if cs[4]:		# if MPT addr list is not empty in web app
					sID_MPTaddr_list[-1][1] += [[long(c4,base=16) for c4 in cs[4]]]
				else:
					sID_MPTaddr_list[-1][1] = None
	# logging.debug("ready to create super commands for: "+str([(dt,sml) for dt,sml in zip(dev_tuples,sID_MPTaddr_list)]))
	# create super command (and sub-commands) for each sID_MPTaddr_list element
	superCmds = [MultiTSuperCmd(dt[0],dt[1],dt[2],sid[0],sid[1]) for (dt,sid) in zip(dev_tuples,sID_MPTaddr_list)]
	logging.debug("super cmds created:")
	for sC in superCmds:
		logging.debug(str(sC))
	# return list of sub-cmds followed by super-cmds.
	# arrange the sub-cmds in the order they should be called
	initRstCmds = [sC.initResetCmd for sC in superCmds]
	addrCmds = [cmd for sC in superCmds for cmd in sC.addrCmds]
	postAddrRstCmds = [sC.postAddrResetCmd for sC in superCmds]
	Tcmds = [cmd for sC in superCmds for cmd in sC.Tcmds]
	postTrstCmds = [sC.postTresetCmd for sC in superCmds]
	allCmds = initRstCmds + addrCmds + postAddrRstCmds + Tcmds + postTrstCmds + superCmds
	# return list
	return allCmds

def TCcmdsFromJSON(JSON):
	cmds = []
	for port in range(1,MAX_NUM_PHYSICAL_PORTS+1):
		tc_json = filter(lambda x: x["type"]=="TC" and x["port"]==port,JSON)
		if tc_json:
			# TODO: what to do with bin and bin_section names?
			cmds += [HubTCCmd(sensorID=[(trh["A_id"],trh["B_id"]) for trh in tc_json],
							  port=port,
							  addy=[(trh["addy"]) for trh in tc_json],
							  convertPy=[(trh["A_convert"],trh["B_convert"]) for trh in tc_json],
							  bias=[(trh["A_bias"],trh["B_bias"]) for trh in tc_json])]
	return cmds

def prepare_json_upload(password, readingTime, cmds):
    return json.dumps({"passwd": password,
                       "datetime": readingTime.strftime("%Y-%m-%d %H%M%S"),
                       "data": reduce(lambda x: x + y.to_JSON_WWW(readingTime), cmds, []), # TODO: filter this to only include replies
                       "errors": []}) # inclue errors here

def limitTo32(JSONlist):
	if len(JSONlist) > 32:
		return [JSONlist[:32]] + limitTo32(JSONlist[32:])
	else:
		return [JSONlist]

class BadHubReplyError(EAMIDexception):
	"""
	Signals that an unparsable response was received by the MID from the hub
	"""
	

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
