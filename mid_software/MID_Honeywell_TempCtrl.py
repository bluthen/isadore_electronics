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
# EA modules
import WWWcomm
import EthModbusComm
# 3rd party modules
import restkit
from daemon import Daemon
import pytz
# std lib modules
import logging
import ConfigParser
import cPickle
import time
import os
import sys
import datetime
import traceback
import gzip

CONFIG_LOC = '../MID.cfg'
LAST_WWW_CONFIG_LOC = 'MID_WWW_Honeywell_TempCtrl'
DATA_BACKUP_LOC = "DATA_BAK"
LOG_LOC = "Honeywell_temp_ctrl.log"

UDC_3300_ID = 12

SP_ID = 21
PV_ID = 20

class MyDaemon(Daemon):
	def run(self):
		try:
			lastWWWcfgDateTime = None
			lastReadingDateTime = None
			lastUploadDateTime = None
			errorState = False
			log_level = logging.INFO

			# load configuration
			config = ConfigParser.ConfigParser()
			config.read(CONFIG_LOC)

			# setup logging
			if config.get("MID","log_level") == "DEBUG":
				log_level = logging.DEBUG
			if config.get("MID","log_level") == "INFO":
				log_level = logging.INFO
			elif config.get("MID","log_level") == "WARNING":
				log_level = logging.WARNING
			elif config.get("MID","log_level") == "ERROR":
				log_level = logging.ERROR
			logging.basicConfig(filename=LOG_LOC, level=log_level, format='%(asctime)s %(message)s')

			# read last WWW configuration saved to disk
			try:
				WWWcfg = readLatestWWWcfg()
			except:
				logging.warning("No WWW config found at " + LAST_WWW_CONFIG_LOC + ".")

			# establish WWW connection
			logging.info("establishing WWW conn")
			MIDname = config.get("HONEYWELL_TEMP_CTRL","MIDname")
			WWWcon = WWWcomm.WWWcomm(config.get("MID","MIDpassword"),
									 config.get("MID","configpath"),
									 config.get("MID","baseurl"),
									 config.get("MID","uploadpath"),
									 config.get("MID","RCstatusPath"),
									 MIDname)
			# get Eth subnet
			ethSubnet = config.get("HONEYWELL_TEMP_CTRL","eth_subnet")

			# 
			# THE MAIN LOOP
			# 
			while(True):
				readingStartTime = datetime.datetime.now()
				# 
				# reload local configuration
				# 
				config.read(CONFIG_LOC)
				# 
				# check shut-off flag
				# 
				if not config.getboolean("MID","turn_off"):
					# 
					# update config from WWW
					# 
					try:
						newWWWcfg = WWWcon.getConfig()
						if newWWWcfg: # if website config updates occured
							WWWcfg = newWWWcfg; logging.debug(str(WWWcfg));
							logging.info("WWW cfg file received.")
							lastWWWcfgDateTime = time.time()
							# 
							# write new cfg to file
							# 
							try:
								writeLatestWWWcfg(WWWcfg)
								logging.info("Wrote WWW cfg to local file")
							except:
								logging.error("Could not write latest WWW configuration to " + LAST_WWW_CONFIG_LOC + ".")
					except:
						logging.error("WWW configuration not received from web server.")

					# 
					# search WWWcfg for read-only commands
					# 
					RO_sensor_tuples = [] # (sID,devTypeID,sensorTypeID,addr)
					for bC_JSON in WWWcfg["burnerControls"]:
						RO_sensor_tuples += [(bC_JSON["sensor_id"],
											  bC_JSON["device_type"],
											  bC_JSON["type"],
											  bC_JSON["addy"])]
					logging.debug("DEBUG: found the following tuples to process"+str(RO_sensor_tuples))
					# 
					# search WWWcfg for remote-control commands
					# 
					RC_sensor_tuples = [] # (ctrlID,sID,value,sensorTypeID,deviceTypeID,addr)
					for bC_JSON in WWWcfg["RC"]:
						RC_sensor_tuples += [(bC_JSON["ctrl_id"],
											  bC_JSON["sensor_id"],
											  bC_JSON["value"],
											  bC_JSON["sensor_type_id"],
											  bC_JSON["device_type_id"],
											  bC_JSON["address"])]
					# 
					# create all RC cmds
					# TODO: use the factory method
					RCcmds = []
					for rcst in RC_sensor_tuples:
						if rcst[4] == UDC_3300_ID:
							if rcst[3] == SP_ID:
								logging.debug("Creating RC cmd for: "+str(rcst))
								RCcmds += [EthModbusComm.Honeywell_UDC3500_setSP(rcst[0],
																				 ethSubnet+"."+str(rcst[5]),
																				 rcst[2])]
					# 
					# create all RO cmds
					# TODO: use the factory method
					# 
					ROcmds = []
					for rost in RO_sensor_tuples:
						if rost[1] == UDC_3300_ID:
							if rost[2] == SP_ID:
								ROcmds += [EthModbusComm.Honeywell_UDC3500_getSP(rost[0],
																				 ethSubnet+"."+str(rost[3]))]
							if rost[2] == PV_ID:
								ROcmds += [EthModbusComm.Honeywell_UDC3500_getPV(rost[0],
																				 ethSubnet+"."+str(rost[3]))]
					# 
					# process all RC cmds and send status updates
					# 
					for rcc in RCcmds:
						try:
							logging.debug("Executing RC cmd: "+rcc.shortDesc())
							rcc.execute()
							WWWcon.RC_cmd_status(rcc.sensorID,True)
						except Exception as e:
							logging.error("Unable to process RC cmd: "+rcc.shortDesc())
							# TODO: try a few more times before giving up
							WWWcon.RC_cmd_status(rcc.sensorID,False)
						time.sleep(4.)
					# 
					# process all RO cmds
					# 
					for roc in ROcmds:
						roc.execute()
						time.sleep(2.) # TODO: is there a way to remove this?
					# 
					# send data to WWW
					# 
					try:
						midPasswd = config.get("MID","MIDpassword")
						WWWcon.uploadReading(midPasswd,datetime.datetime.now(pytz.utc),ROcmds,[])
						logging.info("SUCCESSFULLY UPLOADED DATA")
						lastUploadDateTime = time.time()
						if errorState:
							try:
								# send all readings stored in backup file
								postStoredData(WWWcon)
								logging.info("SUCCESSFULLY UPLOADED STORED DATA")
								# purge data backup file
								purgeStoredData()
								# indicate error state is over
								errorState = False
							except Exception as e:
								logging.critical("An error occured while trying to upload data from error state: "+str(e))
					except Exception as e:
						logging.error("Error occured while uploading results to server: "+str(e))
						# indicate MID is cut off from WWW server
						errorState = True
						# re-instantiate WWW
						WWWcon = WWWcomm.WWWcomm(config.get("MID","MIDpassword"),
												 config.get("MID","configpath"),
												 config.get("MID","baseurl"),
												 config.get("MID","uploadpath"),
												 config.get("MID","RCstatusPath"),
												 MIDname)
					# TODO:send errors to WWW
					lastRun=time.time()
				else:
					logging.warning("Turn off flag set to TRUE")
				# END BLOCK FOR TURN-OFF FLAG CHECK
				# space readings out some minimum amount of time
				min_interval = config.getint("HONEYWELL_TEMP_CTRL","min_reading_interval_seconds")
				readingDuration = datetime.datetime.now() - readingStartTime
				if readingDuration.seconds < min_interval:
					logging.info("taking a break for " + str(min_interval - readingDuration.seconds) + " seconds...")
					time.sleep(min_interval - readingDuration.seconds)
				else:
					logging.error("Unable to keep up with requested reading interval.  Last reading took "+str(readingDuration.seconds)+" > "+str(min_interval)+".")
					# TODO: log that we are unable to meet the desired reading interval
		except Exception as e:
			logging.critical("shit! "+str(e))
			logging.critical(traceback.format_exc())

def writeLatestWWWcfg(WWWcfg):
	f = open(LAST_WWW_CONFIG_LOC,"wb")
	cPickle.dump(WWWcfg,f)

def readLatestWWWcfg():
	f = open(LAST_WWW_CONFIG_LOC,"rb")
	return cPickle.load(f)

def postStoredData(WWWcon):
	try:
		theFile = gzip.open(DATA_BACKUP_LOC,"rb")
	except:
		logging.error("Data backup file could not be opened.")
		raise
	while True:
		try:
			allCmds = cPickle.load(theFile)
			WWWcon.uploadData(allCmds[1],allCmds[0])
			# TODO: examine response code for success indicator
		except EOFError:
			break						# we have reached the end of the file
		except Exception as e:
			logging.critical("Another error.  This time while sending data stored during a previous error.  I am exasperated!"+str(e))
	theFile.close()

def purgeStoredData():
	try:
		os.remove(DATA_BACKUP_LOC)
	except:
		print >> sys.stderr, "I confess to almighty God and to you, my brother or sister, that I have failed to delete the file of stored data."

def processEthCommands(WWWcfg,localConfig,WWWcon):
	RCcmds = [];ROcmds = []
	# create RC cmds
	RCcmds = [EthModbusComm.factory(cmd["device_type_id"],
									cmd["sensor_type_id"],
									cmd["ctrl_id"],
									localConfig.get("MID","eth_subnet")+"."+str(cmd["address"]),
									cmd["value"]) for cmd in WWWcfg["RC"] if EthModbusComm.check(cmd["device_type_id"],cmd["sensor_type_id"])]
	logging.info("Created "+str(len(RCcmds))+" RC Eth cmds.")
	for rcc in RCcmds:
		logging.info(rcc.shortDesc())
	# create read-only (RO) commands
	ROcmds = [EthModbusComm.factory(cmd["device_type"],
									cmd["type"],
									cmd["sensor_id"],
									localConfig.get("MID","eth_subnet")+"."+str(cmd["addy"])) for cmd in WWWcfg["burnerControls"] if EthModbusComm.check(cmd["device_type"],cmd["type"])]
	logging.info("Created "+str(len(ROcmds))+" RO Eth cmds.")
	for roc in ROcmds:
		logging.info(roc.shortDesc())
	# execute commands
	for rc in RCcmds:
		rc.execute()
	# report RC command statuses to WWW
	for rc in RCcmds:
		try:
			WWWcon.RC_cmd_status(rc.sensorID,True)
		except Exception as e:
			logging.error("Failed to report status of RC command: " + rc.shortDesc() + "\n" + str(e))
	for ro in ROcmds:
		ro.execute()
		# time.sleep(5)
	# return list of RO commands
	return ROcmds

def processRS485Commands(WWWcfg,localConfig,WWWcon):
		allRS485Cmds = []
		successfulCmds = []
		# put RC cmds in front of queue
		for dev in WWWcfg["RC"]:
			if not EthModbusComm.check(dev["device_type_id"],dev["sensor_type_id"]): # if not ETH, must be RS485
				allRS485Cmds += [serialComm.cmdFactory(dev["device_type_id"],
													   dev["sensor_type_id"],
													   dev["ctrl_id"], # passed into sensorID
													   dev["address"],
													   dev["value"])]
		# now, add the read-only commands
		for dev in WWWcfg["burnerControls"]:
			if not EthModbusComm.check(dev["device_type"],dev["type"]): # if not ETH, must be RS485
				allRS485Cmds += [serialComm.cmdFactory(dev["device_type"],
													   dev["type"],
													   dev["sensor_id"],
													   dev["addy"])]
		# process RS485 commands
		if localConfig.has_option("MID", "RS485_PORT"):
			sc = serialComm.SerialComm(port=localConfig.get("MID","RS485_PORT"))
			for cmd in allRS485Cmds:
				try:
						sc.processCommand(cmd)
						# if RC cmd, inform web server and don't save the cmd
						if isinstance(cmd,FujiInterface.FujiPXR4SetSVCmd):
								try:
									WWWcon.RC_cmd_status(cmd.ctl_id,1)
								except WWWcomm.MID_RCstatusError:
									logging.error("RC status error")
									pass
						else:
								successfulCmds += [cmd]
				except:
						# todo: write exception info to log file
						# if RC cmd, inform web server and don't save the cmd
						if isinstance(cmd,FujiInterface.FujiPXR4SetSVCmd):
								try:
										WWWcon.RC_cmd_status(cmd.ctl_id,0)
								except WWWcomm.MID_RCstatusError:
										# todo: log this event
										pass
			# done, close serial connection
			sc.closeSer()
		return successfulCmds

# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
