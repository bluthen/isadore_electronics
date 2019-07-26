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
import VFDinterface
import FujiInterface
import hubComm
import WWWcomm
import EthModbusComm
# 3rd party modules
import serialComm
import restkit
from daemon import Daemon
import pytz
# std lib modules
import logging
import hubPackets
import ConfigParser
import cPickle
import gzip
import time
import os
import sys
import datetime
import traceback
import DMMCCmd

CONFIG_LOC = '../MID.cfg'
LAST_WWW_CONFIG_LOC = 'MID_WWW'
DATA_BACKUP_LOC = "DATA_BAK"

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
			logging.basicConfig(filename='./MID.log', level=log_level, format='%(asctime)s %(message)s')

			# read last WWW configuration saved to disk
			try:
				WWWcfg = readLatestWWWcfg()
			except:
				logging.warning("No WWW config found at " + LAST_WWW_CONFIG_LOC + ".")

			# establish sensor hub connection
			try:
				if("hub_serial" in zip(*config.items('MID'))[0]):
					hubCon = hubComm.HubComm(serialPath=config.get("MID", "HUB_SERIAL"))
				else:
					hubCon = hubComm.HubComm(config.get("MID","MID_IP"),
								 config.getint("MID","MID_PORT"),
								 config.get("MID","HUB_IP"),
								 config.getint("MID","HUB_PORT"))
			except Exception as e:
				logging.critical("Unable to establish communication with MID.  Sofware will probably stop now.")
				logging.critical(str(e))
				raise

			# establish WWW connection
			WWWcon = createWWWcon(config)

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
						if newWWWcfg:
							# website config updates occured
							WWWcfg = newWWWcfg; logging.debug(str(WWWcfg));
							logging.info("WWW cfg file received.")
							lastWWWcfgDateTime = time.time()
							# write new cfg to file
							try:
								writeLatestWWWcfg(WWWcfg)
								logging.info("Wrote WWW cfg to local file")
							except:
								logging.error("Could not write latest WWW configuration to " + LAST_WWW_CONFIG_LOC + ".")
					except:
						logging.error("WWW configuration not received from web server.")
					# 
					# generate and process all EA sensor unit commands
					# that should be processed
					# 
					# buid commands from JSON
					allCmds=[]
					try:
						logging.info("Creating commands from JSON received from WWW.")
						allCmds = hubComm.allCmdsFromJSON(WWWcfg)
					except Exception as e:
						logging.error("Error occured while creating commands: "+str(e))
					# process commands and record errors
					allErrs = []		# storage place for all errors 
					for cmdi,cmd in enumerate(allCmds):
						try:
							logging.info("Processing command "+
										 str(cmdi+1)+" of "+str(len(allCmds))+"...")
							allErrs += [hubCon.processCommand(cmd)]
						except hubComm.BadHubReplyError:
							logging.warning("Bad hub reply, reporting error to WWW for all sensors in cmd.")
							# report error for all sensor IDs, will be the only one reported
							allErrs += [hubPackets.HubErrorResponse()]
							allErrs[-1].addParseErrors(cmd.getSensorIDs())
							# clean up communications
							hubCon.clearComm()
						except hubPackets.HubTimeoutError:
							logging.warning("Timed out waiting for hub reply, reporting error to WWW for all sensors in cmd.")
							# report error for all sensor IDs, it will be the only one reported
							allErrs += [hubPackets.HubErrorResponse()]
							allErrs[-1].addTimeoutError(cmd.getSensorIDs())
							# clean up communications
							hubCon.clearComm()
						# log command
						# logging.debug(str(cmd))

					# 
					# create and process commands for Ethernet devices
					# 
					successfulEthCmds = processEthCommands(WWWcfg,config,WWWcon)
					allCmds += successfulEthCmds
					# 
					# create and process read commands for RS485 devices
					# 
					# TODO: FIX THIS!!!
					successfulRS485Cmds = processRS485Commands(WWWcfg,config,WWWcon)
					allCmds += successfulRS485Cmds
					# 
					# handle the special case AB EtherNet/IP hack
					# 
					try:
						logging.info("Attempting the A-B VFD hack.")
						AB_VFDs = VFDinterface.ABinterfaceFactory(WWWcfg)
						for i in AB_VFDs:
							i.update()
						allCmds.extend(AB_VFDs)
					except Exception as e:
						logging.error("Error occured while reading the AB VFD parameters:"+str(e))


					try:
						dmcmds = DMMCCmd.processDMMCCommands(WWWcfg["commandInfo"])
						allCmds += dmcmds
						logging.info('Read from DryerMaster: '+str(len(dmcmds)))
					except Exception as e:
						logging.error("Error occured while trying to read the Dryer Master's MC: ")
						logging.exception(e)


					lastReadingDateTime = time.time()
					# 
					# send data to WWW
					# 
					try:
						midPasswd = config.get("MID","MIDpassword")
						WWWcon.uploadReading(midPasswd,datetime.datetime.now(pytz.utc),allCmds,allErrs)
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
						# save latest reading to backup file
						try:
							storeReading(allCmds,DATA_BACKUP_LOC)
						except:
							logging.error("Cannot write to backup data location.")
						# re-instantiate WWW
						WWWcon = createWWWcon(config)
					# TODO:send errors to WWW
					lastRun=time.time()
					# store raw data if instructed to do so
					if config.getboolean("MID","STORE_RAW_DATA_MODE"):
						storeReading(allCmds,config.get("MID","RAW_DATA_LOC"))
				else:
					logging.info("Turn off flag set to TRUE")
				# END BLOCK FOR TURN-OFF FLAG CHECK
				# space readings out some minimum amount of time
				min_interval = config.getint("MID","min_reading_interval_seconds")
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

def createWWWcon(config):
	# establish WWW connection
	try:
		MIDname = config.get("MID","MIDname")
	except:
		MIDname = None
	return WWWcomm.WWWcomm(config.get("MID","MIDpassword"),
						   config.get("MID","configpath"),
						   config.get("MID","baseurl"),
						   config.get("MID","uploadpath"),
						   config.get("MID","RCstatusPath"),
						   MIDname)

def storeReading(allCmds,fileLoc):
	if os.path.exists(fileLoc):
		theFile = gzip.open(fileLoc,"ab")
	else:
		theFile = gzip.open(fileLoc,"wb")
	cPickle.dump([datetime.datetime.now(pytz.utc),allCmds],theFile)
	theFile.close()

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
