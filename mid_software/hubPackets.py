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
import struct
from conversion import evalConversion
import operator
import hacks
from EAMIDexception import EAMIDexception
import numpy as np
import logging

MAGIC = "DERV"
MAX_NUM_PHYSICAL_PORTS = 6
PRESSURE_SAMPLES_PER_READING = 10
MAX_NUM_MPT_PTS = 6

class HubPing:
	def __init__(self,pingVal):
		self.pingVal = pingVal
		self.pongVal = None

	def createPacket(self):
		return MAGIC+struct.pack("B",130)+struct.pack("<H",self.pingVal)

	def processReply(self,rplyData):
		try:
			rplyCode = ord(rplyData.read(1))
		except:					# presume nothing more to process
			raise EmptyHubRplyError(self,rplyData.getvalue())
		self.pongVal = struct.unpack("<H",rplyData.read(2))[0]

	def check(self):
		return self.pingVal+1 == self.pongVal

class HubCmd:
	TEMP_HUM_CODE = 1;	WIND_CODE = 2;	TACH_CODE = 3;	TC_K_CODE = 6;	PRESSURE_CODE = 7;	PRESSURE_WIDE_CODE = 8; MULTI_T_RST_CODE = 9; MULTI_T_CODE_BASE = 9; MULTI_T_ADDR_CODE_BASE = 13;
	TEMP_HUM_SZ = 4; WIND_SZ = 2; TACH_SZ = 2; TC_K_SZ = 4; PRESSURE_SZ = 2; PRESSURE_WIDE_SZ = 4; MULTI_T_RST_SZ = 1; MULTI_T_SZ = 2; MULTI_T_ADDR_SZ = 8;
	GENERAL_UNIT_READING_CMD = 25
	

	def __init__(self, sensorID, port=0, R=0, addy=list(), cmd=0, convertPy=list(), bias=list(),binName=[],binSectionName=[]):
		"""
		Constructor
		"""
		self.startPos = None
		self.port = port
		self.addy = addy
		self.cmd = cmd
		self.R = R
		self.sensorID = sensorID
		self.convertPy = convertPy
		self.bias = bias
		self.binName = binName
		self.binSectionName = binSectionName
		self.rplyCode = 0
		self.rplySize = 0
		self.rplyTotalSize = 0
		self.retCmdCode = 0
		self.rplyAddrLen = -1

		# TODO: move check to subclasses that need this
		# # check to make sure there is an equal number of addys, convert functions, biases provided
		# if not all([x == len(addy) for x in (len(convertPy),len(bias))]):
		# 	raise PacketCreationError("Unequal number of addresses, convert functions, and/or biases provided to Packet constructor")

	def createPacket(self):
		logging.debug("Creating a packet with cmd code = "+str(self.cmd))
		buffer = MAGIC
		buffer += struct.pack("B",HubCmd.GENERAL_UNIT_READING_CMD)
		buffer += struct.pack("B",self.cmd)
		buffer += struct.pack("B",self.R)
		buffer += struct.pack("B",self.port)
		buffer += struct.pack("B",len(self.addy))
		for i in self.addy:
			buffer += struct.pack("<H",i)

		return buffer

	def processReply(self,rplyBuf):
		# record starting location of rply data
		self.startPos = rplyBuf.tell()
		# grab the first byte (rply code)
		firstByte = rplyBuf.read(1)
		# if empty, exit via exception
		if not firstByte:
			raise EmptyHubRplyError(self,rplyBuf.getvalue())
		# parse hub rply code
		self.rplyCode = ord(firstByte)
		# if not a readings rply, go to start of rply data and throw exception
		if self.rplyCode != 1:
			rplyBuf.seek(self.startPos)
			raise HubRplyCmdError(self,rplyBuf.getvalue())
		# parse rply size
		self.rplySize = ord(rplyBuf.read(1))
		# compute total size (DATA + 3B)
		self.totalSize = self.rplySize + 3
		# TODO: check against an expected size
		# parse rply CC
		self.retCmdCode = ord(rplyBuf.read(1))
		# if rply CC doesn't match sent CC, throw exception
		if self.retCmdCode != self.cmd:
			raise HubRplyCCError(self,rplyBuf,self.startPos,self.totalSize) # DATA + 3B
		# all readings replies begin with the number of addresses with replies
		# parse the number of addresses with replies
		self.rplyAddrLen = ord(rplyBuf.read(1))
		# if addy lengths don't match, throw exception
		if self.rplyAddrLen != len(self.addy):
			raise HubRplyAddrErr(self,rplyBuf,self.startPos,self.totalSize)

	def getSensorIDs(self):
		# a generic version that assumes self.sensorIDs is just a list of IDs
		# must be overloaded if this is not the case for a given child class
		return [sID for sID in self.sensorID]
	
	def __str__(self):
		return "command info\n" + "===================\n" + "bin name: " + str(self.binName) + "\nbin section name: " + str(self.binSectionName) + "\nsensor ID: " + str(self.sensorID) + "\nport: " + str(self.port) + "\naddresses: " + str(self.addy) + "\ncommand code: " + str(self.cmd) + "\nreply code: " + str(self.rplyCode) + "\nreply size: " + str(self.rplySize) + "\nreply command code: " + str(self.retCmdCode) + "\nreply addy length: " + str(self.rplyAddrLen)

class HubTempHumCmd(HubCmd):
	def __init__(self,sensorID,port=0,addy=list(),convertPy=[("x","x")],bias=[(0,0)],binName=[],binSectionName=[]):
		"""
		sensorID: [(T1_sid,RH1_sid),(T2_sid,RH2_sid),...,(TN_sid,RHN_sid)]
		"""
		HubCmd.__init__(self,sensorID,port,HubCmd.TEMP_HUM_SZ,addy,HubCmd.TEMP_HUM_CODE,convertPy,bias,binName,binSectionName)
		self.tempRaw = list()
		self.humidityRaw = list()
		self.tempEng = list()
		self.humidityEng = list()

	def to_JSON_WWW_data(self,readingTime):
		retVal = []
		for (sid,tempRaw,tempEng,rhRaw,rhEng) in zip(self.sensorID,
													 self.tempRaw,
													 self.tempEng,
													 self.humidityRaw,
													 self.humidityEng):
			retVal += [{"sensor_id":sid[0],
						"type":"SHT_T",
						"value":tempEng,
						"raw_data":tempRaw,
						"datetime":readingTime.isoformat()},
					   {"sensor_id":sid[1],
						"type":"SHT_RH",
						"value":rhEng,
						"raw_data":rhRaw,
						"datetime":readingTime.isoformat()}]
			# insert an error code if error detected
			# TODO: check error code using raw value (see Russ's email)
			# TODO: how to check for no response from unit?
			if tempEng < -39.0:
				logging.info("INFO: default value returned for SHT with sensor id "+str(sid[0]))
				retVal[-2]["error_code"] = 185
				retVal[-1]["error_code"] = 185
		return retVal

	def processReply(self,rplyBuf):
		# list of indices of bad eng vals
		badEng = []; badEng_msg = [];
		# let the parent class fill in some stuff
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		# for each unit's reply...
		for sid,i in zip(self.sensorID,range(self.rplyAddrLen)):
			try:
				(rawTemp, rawHum) = struct.unpack("<HH",rplyBuf.read(4))
				self.tempRaw.append(rawTemp)
				self.humidityRaw.append(rawHum)
			except EAMIDexception as e:
				raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)
			try:
				(t,h)=self.computeEngVals(i, rawTemp, rawHum)
			except EAMIDexception as e:
				t = 0; h = 0;
				badEng += [sid[0],sid[1]]
				badEng_msg += [str(e),str(e)]
			self.tempEng.append(t)
			self.humidityEng.append(h)
		# raise exception if bad eng val detected
		if len(badEng) > 0:
			raise HubRplyEngValueError(badEng,badEng_msg)

	def computeEngVals(self, index, rawTemp, rawHum):
		'''%returns (eng temp, eng RH)'''
		t=0;h=0;
		t = evalConversion(self.convertPy[index][0], rawTemp)+float(self.bias[index][0])
		h = evalConversion(self.convertPy[index][1], rawHum, t)+float(self.bias[index][1])
		return (t,h)

	def toWWWparam(self):
		# DEPRICATED
		sensorIDstring = ",".join([str(x[0]) for x in self.sensorID]) + "," + ",".join([str(x[1]) for x in self.sensorID])
		return (sensorIDstring,",".join([str(x) for x in (self.tempRaw + self.humidityRaw)]),",".join([str(x) for x in (self.tempEng + self.humidityEng)]))

	def getSensorIDs(self):
		return [x[0] for x in self.sensorID] + [x[1] for x in self.sensorID]

	def __str__(self):
		return "T/RH cmd\n"+HubCmd.__str__(self) + "\nreply temperatures: " + str(self.tempRaw) +	"\nreply humidities: " + str(self.humidityRaw)

	def toASCII(self,index):
		"""See parent's description"""
 		return "Temperature: "+str(self.tempEng[index])+"F\nRelative humidity: "+str(self.humidityEng[index])+"%"

class HubTachCmd(HubCmd):
	# NOTE: Raw value from unit is the engineering value
	def __init__(self,sensorID,port=0,addy=list(),convertPy=None,bias=list(),binName=[],binSectionName=[]):
		# no conversion, just fill with junk
		if not convertPy:
			convertPy = [None] * len(addy)
		HubCmd.__init__(self,sensorID,port,HubCmd.TACH_SZ,addy,HubCmd.TACH_CODE,convertPy,bias,binName,binSectionName)
		self.RPM = list()

	def to_JSON_WWW_data(self,readingTime):
		retVal = []
		for (sid,rpm) in zip(self.sensorID,self.RPM):
			retVal += [{"sensor_id":sid,
						"type":"tach",
						"value":rpm,
						"raw_data":rpm,
						"datetime":readingTime.isoformat()}]
		return retVal

	def processReply(self,rplyBuf):
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				RPM = struct.unpack("<H",rplyBuf.read(2))[0]
				self.RPM.append(RPM)
		except:
			raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)

	def toWWWparam(self):
		# DEPRICATED
		return (",".join([str(x) for x in self.sensorID]),
				",".join([str(x) for x in self.RPM]),
				",".join([str(x) for x in self.RPM]))

	def __str__(self):
		return "Tachometer command\n"+HubCmd.__str__(self) + "\nreply RPMs: " + str(self.RPM)

class HubTCCmd(HubCmd):
	def __init__(self,sensorID,port=0,addy=list(),convertPy=(("x",),("x",)),bias=((0,),(0,)),binName=[],binSectionName=[]):
		HubCmd.__init__(self,sensorID,port,HubCmd.TC_K_SZ,addy,HubCmd.TC_K_CODE,convertPy,bias,binName,binSectionName)
		self.T1_raw = list()
		self.T2_raw = list()
		self.T1_eng = list()
		self.T2_eng = list()

	def to_JSON_WWW_data(self,readingTime):
		retVal = []
		for (sid,t1Raw,t1Eng,t2Raw,t2Eng) in zip(self.sensorID,
												 self.T1_raw,
												 self.T1_eng,
												 self.T2_raw,
												 self.T2_eng):
			if sid[0]:
				retVal += [{"sensor_id":sid[0],
							"type":"TC_A",
							"value":t1Eng,
							"raw_data":t1Raw,
							"datetime":readingTime.isoformat()}]
			if sid[1]:
				retVal += [{"sensor_id":sid[1],
							"type":"TC_B",
							"value":t2Eng,
							"raw_data":t2Raw,
							"datetime":readingTime.isoformat()}]
		return retVal

	def getSensorIDs(self):
		return [x[0] for x in self.sensorID if x[0]] + [x[1] for x in self.sensorID if x[1]]

	def processReply(self,rplyBuf):
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				(raw1,raw2) = struct.unpack("<HH",rplyBuf.read(4))
				self.T1_raw.append(raw1)
				self.T2_raw.append(raw2)
		except:
			raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)
		try:
			self.computeEngVals()
		except HubRplyEngValueError:
			raise

	def computeEngVals(self):
		badEng_sID = []; badEng_msg = []
		for T_eng,sIDs,cPs,Ts,bs in zip((self.T1_eng,self.T2_eng),
									   ([sid[0] for sid in self.sensorID],
										[sid[1] for sid in self.sensorID]),
									   ([cP[0] for cP in self.convertPy],
										[cP[1] for cP in self.convertPy]),
									   (self.T1_raw,self.T2_raw),
									   ([b[0] for b in self.bias],
										[b[1] for b in self.bias])):
			for sid,cP,T,b in zip(sIDs,cPs,Ts,bs):
				try:
					logging.debug("pre TC eval conversion:"+str(sid)+str(cP)+str(T)+str(b))
					if cP:
						T_eng += [evalConversion(cP,T) + b]
					else:		# if no conversion formula given, just give raw value
						T_eng += [T]
				except Exception as e:
					# log the offending sensor id and error msg
					badEng_sID += [sid]
					badEng_msg += [str(e)]
					# insert garbage value
					T_eng += [0]
					# log this incident
					logging.info("Exception occured during computation of TC eng value."+str(e)+"\n"+str(sid)+str(cP)+str(T)+str(b))
		if len(badEng_sID) > 0:
			raise HubRplyEngValueError(badEng_sID,badEng_msg)
	def toWWWparam(self):
		# DEPRICATED
		# create List of (ID,raw,eng), filter out elements with None for sensorID, break into seperate lists of each ID, raw, eng, then create a string for each of the seperate lists, and return a list of those strings
		return map(lambda x: reduce(lambda y,z: str(y)+","+str(z),
									x),
				   zip(*(filter(lambda x: x[0],
								[y for x in [zip(*x) for 
											 srree in zip(self.sensorID,
														  zip(self.T1_raw,self.T2_raw),
														  zip(self.T1_eng,self.T2_eng))] for 
								 y in x])))) # Russ's favorite line of code in all the MID software!  My only regret is that I didn't write this in LISP.

	def __str__(self):
		return "Thermocouple command\n"+HubCmd.__str__(self) + "\nraw T1: " + str(self.T1_raw) + "\nT1 eng temp: " + str(self.T1_eng) + "\nraw T2: " + str(self.T2_raw) + "\nT2 eng temp: " + str(self.T2_eng)

class HubPressureWideSuperCmd(HubCmd):

	def __init__(self):
		HubCmd.__init__(self,0)
		self.cmds = []
		self.samples = {}

	def createPacket(self):
		"""Do nothing. Constituent cmds will handle this."""
		return None

	def processReply(self,rplyBuf):
		"""Do nothing. Constituent cmds will handle this."""
		pass

	def createCmds(self,JSON):
		for smpl in range(PRESSURE_SAMPLES_PER_READING):
			for port in range(1,MAX_NUM_PHYSICAL_PORTS+1):
				kpa_json = filter(lambda x: x["type"]=="pressure" and x["port"]==port,JSON)
				if kpa_json:
					# TODO: what to do with bin and bin_section names?
					self.cmds += [HubPressureWideCmd(sensorID=[trh["sensor_id"] for trh in kpa_json],
													 port=port,
													 addy=[(trh["addy"]) for trh in kpa_json],
													 convertPy=[trh["convert"] for trh in kpa_json],
													 bias=[trh["bias"] for trh in kpa_json])]
		return self.cmds

	def collectSamples(self):
		# TODO: maybe have a minimum number of readings
		self.samples = {}
		for cmd in self.cmds:
			for sample in zip(cmd.sensorID,cmd.raw,cmd.eng):
				try:
					self.samples[sample[0]]["raw"] += [sample[1]]
					self.samples[sample[0]]["eng"] += [sample[2]]
				except KeyError:
					self.samples[sample[0]] = {"raw":[sample[1]],"eng":[sample[2]]}

	def to_JSON_WWW_data(self,readingTime):
		# compute averages
		self.collectSamples()
		return [{"sensor_id":sample[0],
				 "type":"pressure_wide_super",
				 "datetime":readingTime.isoformat(),
				 "value":np.mean(sample[1]["eng"]),
				 "raw_data":np.mean(sample[1]["raw"])} for sample in self.samples.items() if sample[1]["eng"] != None] # filtering by None eng vals will hopefully prevent inclusion of errors

class HubPressureWideCmd(HubCmd):
	def __init__(self,sensorID,port=0,addy=list(),convertPy=["x"],bias=[0],binName=[],binSectionName=[]):
		HubCmd.__init__(self,sensorID,port,HubCmd.PRESSURE_WIDE_SZ,addy,HubCmd.PRESSURE_WIDE_CODE,convertPy,bias,binName,binSectionName)
		self.raw = list()
		self.eng = list()

	def computeEngVals(self):
		badEng_sID = []; badEng_msg = [];
		for sID,cP,raw,b in zip(self.sensorID,self.convertPy,self.raw,self.bias):
			try:
				self.eng += [evalConversion(cP,raw) + b]
			except Exception as e:
				# log the offending sensor ID and error msg
				badEng_sID += [sID]
				badEng_msg += [str(e)]
				# insert garbage value
				self.eng += [None]
		if len(badEng_sID) > 0:
			raise HubRplyEngValueError(badEng_sID,badEng_msg)

	def processReply(self,rplyBuf):
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				rawTmp = struct.unpack("<I",rplyBuf.read(4))[0]
				self.raw.append(rawTmp)
		except:
			raise HubRplyParseError(self,rplyBuf.getvalue(),self.startPos,self.totalSize)
		try:
			self.computeEngVals()
		except HubRplyEngValueError:
			raise

	def to_JSON_WWW_data(self,readingTime):
		return []				# do nothing, let the super pressure wide class handle JSON output

	def __str__(self):
		return "Presurewide command\n"+HubCmd.__str__(self) + "\nreply raw: " + str(self.raw) + "\nreply eng: " + str(self.eng)

class MultiTResetCmd(HubCmd):
	def __init__(self,port=0,addy=list()):
		HubCmd.__init__(self,[],port,HubCmd.MULTI_T_RST_SZ,addy,HubCmd.MULTI_T_RST_CODE)
		self.replies = []

	def to_JSON_WWW_data(self,readingTime):
		return []

	def getSensorIDs(self):
		return [sID for sID in self.sensorID]

	def processReply(self,rplyBuf):
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				self.replies += [ord(rplyBuf.read(1))]
		except:
			raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)
		# TODO: throw errors if len(replies) = len(addys)

	def toWWWparam(self):
		return []

	def __str__(self):
		return "Multi-pt Temp reset command\n"+HubCmd.__str__(self)+"\nReplies T: "+str(self.replies)

	def shortDesc(self):
		return "Multi-pt T cmd\nAddrs:"+str(self.addy)

class MultiTcmd(HubCmd):
	def __init__(self,sensorID,channel,port=0,addy=list(),convertPy=[],bias=[]):
		HubCmd.__init__(self,sensorID,port,HubCmd.MULTI_T_SZ,addy,
						HubCmd.MULTI_T_CODE_BASE+channel,convertPy=convertPy,bias=bias)
		self.raw = []
		self.eng = []
		self.channel = channel

	def to_JSON_WWW_data(self,readingTime):
		return []

	def getSensorIDs(self):
		return [sID for sID in self.sensorID]

	def processReply(self,rplyBuf):
		# badEng_sID = []; badEng_msg = []
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				self.raw += [struct.unpack("<H",rplyBuf.read(HubCmd.MULTI_T_SZ))[0]]
		except:
			raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)
		# TODO: record some sort of error if unexpected 0xFFFF reply
		# self.eng = []
		# for (cP,r,b) in zip(self.convertPy,self.raw,self.bias):
		# 	try:
		# 		self.eng += [evalConversion(cP,r) + b]
		# 	except Exception as e:
		# 		# log the offending sensor ID and error msg
		# 		badEng_sID += [sID]
		# 		badEng_msg += [str(e)]
		# 		# insert garbage value
		# 		self.eng += [None]
		self.eng = [ds18b20_conversion(r) for r in self.raw]
		# if len(badEng_sID) > 0:
		# 	raise HubRplyEngValueError(badEng_sID,badEng_msg)

	def __str__(self):
		return "Multi-pt Temp command\n"+HubCmd.__str__(self)+"\nRaw: "+str(self.raw)+"\nEng: "+str(self.eng)

	def shortDesc(self):
		return "Multi-pt T cmd\nAddrs:"+str(self.addy)

def ds18b20_conversion(v):
	neg = 1.0
	if(v & 0xF800):
		neg=-1.0
		v=~v+1
	digits = (v&0x07F0) >> 4
	decimals = v & 0x000F
	C = neg*(digits + decimals/16.0)
	return 1.8 * C + 32.0
	
class MultiTSuperCmd(HubCmd):
	# this is to handle collection of readings for a single MPT cable
	def __init__(self,port,devAddy,MPTchannel,sensorIDs,MPTaddys):
		# TODO: enforce that len of sensorIDs and MPTaddys lenths is the same
		HubCmd.__init__(self,0,port,addy=[devAddy])
		self.MPTchannel = MPTchannel
		self.sensorIDs = sensorIDs
		self.MPTaddys = MPTaddys
		# create initial reset command
		self.initResetCmd = MultiTResetCmd(port=self.port,addy=self.addy)
		# create commands to get MAX_NUM_MPT_PTS addresses from this port/addr/channel
		self.addrCmds = []
		for pti in range(MAX_NUM_MPT_PTS):
			self.addrCmds += [MultiTAddrCmd([0],self.MPTchannel,self.port,self.addy)]
		# create post-addr collection reset cmd
		self.postAddrResetCmd = MultiTResetCmd(port=self.port,addy=self.addy)
		# create commands to get MAX_NUM_MPT_PTS temperature readings from this port/addr/channel
		# TODO: !!!bias and convert from web app are unused!!!
		self.Tcmds = [MultiTcmd(sensorID=[0], channel=self.MPTchannel,
								port=self.port, addy=self.addy,
								convertPy=["x"], bias=[0]) for i in range(MAX_NUM_MPT_PTS)]
		# create post-temperature collection reset cmd
		self.postTresetCmd = MultiTResetCmd(port=self.port,addy=self.addy)

	def createPacket(self):
		return None

	def to_JSON_WWW_data(self,readingTime):
		logging.debug("preparing MPT super cmd upload...")
		sID_MPTaddr_engVal_list = []; missing_sIDs = []
		logging.debug(self.MPTaddys)
		if self.MPTaddys != None:		# if MPT addresses in web app is not an empty list
			for sID,MPTaddrLst in zip(self.sensorIDs,self.MPTaddys):
				match_sid_p = False
				for MPTaddr in MPTaddrLst:
					match_p = False
					for addrCmd,Tcmd in zip(self.addrCmds,self.Tcmds):
						if long(addrCmd.addrs[0]) == MPTaddr:
							match_p = True; match_sid_p = True;
							sID_MPTaddr_engVal_list += [(sID, addrCmd.addrs[0], Tcmd.eng[0])]
					if not match_p:
						logging.warning("WARNING: No MPT match for sID=" + str(sID)+" ,MPTaddr="+str(hex(MPTaddr))+" ,MPTch="+str(self.MPTchannel)+" ,unitAddr="+str(self.addy[0]))
						logging.debug("DEBUG: returned addresses:")
						for addrCmd in self.addrCmds:
							logging.debug(hex(addrCmd.addrs[0]))
				if not match_sid_p:
					missing_sIDs += [sID]
		else: 					# if MPT addresses in web app is an empty list, just grab them all
			logging.debug("DEBUG: empty address list, will just return all temperatures")
			for addrCmd,Tcmd in zip(self.addrCmds,self.Tcmds):
				logging.debug("MPT addy "+ str(hex(addrCmd.addrs[0])) + " found.")
				if addrCmd.addrs[0] != 0xffffffffffffffffL:
					sID_MPTaddr_engVal_list += [(self.sensorIDs[0], addrCmd.addrs[0], Tcmd.eng[0])]
		retVal = []
		for smel in sID_MPTaddr_engVal_list:
			retVal += [{"sensor_id":smel[0],
						"type":"MPT",
						"value":smel[2],
						"raw_data":smel[2],
						"datetime":readingTime.isoformat()}]
			# check eng value for default value
			# TODO: use raw value to check for default value
			if smel[2] > 180.0:
				retVal[-1]["error_code"] = 185
				logging.warning("WARNING: default MPT value returned for sensor id "+str(smel[0]))
		for missing_sID in missing_sIDs:
			retVal += [{"sensor_id":missing_sID,
						"type":"MPT",
						"error_code":1,
						"datetime":readingTime.isoformat()}]
			# logging.warning("WARNING: missing MPT value for sensor id "+str(smel[0]))
		logging.debug(retVal)
		return retVal

	def processReply(self,rplyBuf):
		pass

	def __str__(self):
		return "Multi-pt Super command\n"+HubCmd.__str__(self)+"\nUnit port: "+str(self.port)+"\nUnit addr: "+str(self.addy[0])+"\nMPT ch: "+str(self.MPTchannel)+"\nMPT addrs: "+str(self.MPTaddys)

class MultiTAddrCmd(HubCmd):
	def __init__(self,sensorID,channel,port=0,addy=list()):
		HubCmd.__init__(self,sensorID,port,HubCmd.MULTI_T_ADDR_SZ,addy,
						HubCmd.MULTI_T_ADDR_CODE_BASE+channel)
		self.addrs = []
		self.channel = channel

	def to_JSON_WWW_data(self,readingTime):
		return []

	def getSensorIDs(self):
		return [sID for sID in self.sensorID]

	def processReply(self,rplyBuf):
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				self.addrs += [struct.unpack("<Q",rplyBuf.read(HubCmd.MULTI_T_ADDR_SZ))[0]]
		except:
			raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)
		# TODO: record some sort of error if unexpected 0xFFFFF reply

	def __str__(self):
		return "Multi-pt T address command\n"+HubCmd.__str__(self)+"\nSensor addresses: "+str(self.addrs)

	def shortDesc(self):
		return "Multi-pt T address cmd\nAddrs:"+str(self.addrs)

class HubWindCmd(HubCmd):
	def __init__(self,sensorID,port=0,addy=list(),convertPy=list(),bias=list(),binName=[],binSectionName=[]):
		HubCmd.__init__(self,sensorID,port,HubCmd.WIND_SZ,addy,HubCmd.WIND_CODE,convertPy,bias,binName,binSectionName)
		self.wind = list()
		self.windEng = list()

	def processReply(self,rplyBuf):
		try:
			HubCmd.processReply(self,rplyBuf)
		except:
			raise
		try:
			for i in range(self.rplyAddrLen):
				rawWind = struct.unpack("<H",rplyBuf.read(2))[0]
			self.wind.append(rawWind)
			self.computeEngVals()
		except:
			raise HubRplyParseError(self,rplyBuf,self.startPos,self.totalSize)

	def computeEngVals(self):
		try:
			self.windEng = map(operator.add,map(evalConversion,self.convertPy,self.wind),self.bias)
			# self.windEng = map(evalConversion,self.convertPy,map(operator.add,self.wind,self.bias))
		except:
			logging.debug("Exception while computing wind engineering values.")
			logging.debug(str(self.convertPy)+';raw='+str(self.wind)+';bias='+str(self.bias))
			self.windEng=[None]*len(self.wind)

	def to_JSON_WWW_data(self,readingTime):
		retVal = []
		for (sid,raw,eng) in zip(self.sensorID,
								 self.wind,
								 self.windEng):
			retVal += [{"sensor_id":sid,
						"type":"wind",
						"value":eng,
						"raw_data":raw,
						"datetime":readingTime.isoformat()}]
		return retVal

	def __str__(self):
		return HubCmd.__str__(self) + "\nreply wind: " + str(self.wind)

class HubErrorResponse:

	HUB_ERROR_RPLY_CODE = 4
	HUB_ERROR_CODES = (1,2,3,4,5,6,7,8,10)
	TIMEOUT_ERROR_CODE = 9
	PARSE_ERROR_CODE = 51
	ENG_VAL_ERROR_CODE = 52

	def __init__(self):
		self.codes = list()
		self.addys = list()

	def isEmpty_p(self):
		if self.codes:
			return False
		else:
			return True

	def processReply(self, rplyBuf):
		startPos = rplyBuf.tell()
		# raise exception if not an error reply
		if ord(rplyBuf.read(1)) != HubErrorResponse.HUB_ERROR_RPLY_CODE:
			rplyBuf.seek(startPos)
			raise NotHubErrorCodeError(None,rplyBuf.getvalue())
		# parse reply
		self.rplySize = ord(rplyBuf.read(1))
		for i in range(self.rplySize):
			self.codes.append(struct.unpack("B", rplyBuf.read(1)))
			self.addys.append(struct.unpack("B", rplyBuf.read(1)))

	def addEngValErrors(self,indices):
		self.codes += [HubErrorResponse.ENG_VAL_ERROR_CODE] * len(indices)
		self.addys += indices

	def addParseErrors(self,sensorIDs):
		self.codes += [HubErrorResponse.PARSE_ERROR_CODE] * len(sensorIDs)
		self.addys += sensorIDs

	def addTimeoutError(self,sensorIDs):
		self.codes += [HubErrorResponse.TIMEOUT_ERROR_CODE] * len(sensorIDs)
		self.addys += sensorIDs

	def __str__(self):
		return "error codes: " + str(self.codes) + "\nerror addys: " + str(self.addys)

class PacketCreationError(EAMIDexception):
	def __init__(self,msg):
		self.msg = msg
	def __str__(self):
		return str(type(self)) + " -- " + self.msg

class HubRplyError(EAMIDexception):
	def __init__(self,theCmd,rplyData):
		Exception(self,theCmd,rplyData)
		self.theCmd = theCmd
		self.rplyData = rplyData

class HubRplyFatalError(HubRplyError):
	def __init__(self,theCmd,rplyData,startPos,packetSize):
		HubRplyError.__init__(self,theCmd,rplyData)
		self.startPos = startPos
		self.packetSize = packetSize

class HubRplyEmptyError(EAMIDexception):
	"""
	"""
	def __str__(self):
		return "I am a HubRplyEmptyError"

class EmptyHubRplyError(HubRplyError):
	"""
	"""
class HubRplyCmdError(HubRplyError):
	"""
	"""

class HubRplyCCError(HubRplyFatalError):
	""" bad reply CC exception """
class HubRplyAddrErr(HubRplyFatalError):
	""" incorrect number of reply addresses exception """
class HubRplyValueError(HubRplyError):
	"""
	"""
class HubRplyParseError(HubRplyFatalError):
	""" generic parsing error """
class HubRplyEngValueError(HubRplyError):
	"""
	"""
	def __init__(self,idxs,msgs):
		self.idxs = idxs
		self.msgs = msgs
class NotHubErrorCodeError(HubRplyError):
	"""
	"""
class HubTimeoutError(EAMIDexception):
	"""Exception for when hub times out."""

def passPacket(rplyBuf,startPos,pktSz):
	""" pass over entire packet in the rply buffer.  works via side effect """
	# move to start of packet
	rplyBuf.seek(startPos)
	# move pktSz Bytes to end of packet
	rplyBuf.seek(startPos+pktSz)
		
# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
