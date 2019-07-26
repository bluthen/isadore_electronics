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
import RTM2000Cmd as RTMcmd
# 3rd party modules
from daemon import Daemon
import pytz
# std lib modules
import logging
import ConfigParser
import cPickle
import time
import sys
import datetime
import traceback

CONFIG_LOC = '../MID_RTM_2000.cfg'
LAST_WWW_CONFIG_LOC = 'MID_RTM_2000_interface_WWW'
LOG_LOC = "RTM_2000_interface.log"

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
            MIDname = config.get("MID","MIDname")
            WWWcon = WWWcomm.WWWcomm(config.get("MID","MIDpassword"),
                                     config.get("MID","configpath"),
                                     config.get("MID","baseurl"),
                                     config.get("MID","uploadpath"),
                                     config.get("MID","RCstatusPath"),
                                     MIDname)
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
                # ##################################################
                # READ FROM RTM2000
                RTMcmds = RTMcmd.createCommands(WWWcfg["commandInfo"],
                                                config.get("MID","RS485_PORT"),
                                                logging)
                for cmd in RTMcmds:
                    cmd._readTemps()
                # END READ FROM RTM2000
                # ##################################################
                # ##################################################
                # UPLOAD DATA
                try:
                    midPasswd = config.get("MID","MIDpassword")
                    WWWcon.uploadReading(midPasswd,datetime.datetime.now(pytz.utc),RTMcmds,[])
                    logging.info("SUCCESSFULLY UPLOADED DATA")
                    lastUploadDateTime = time.time()
                except Exception as e:
                    logging.error("Exception during data upload: "+str(e))
                # END UPLOAD DATA
                # ##################################################
                # ##################################################
                # SPACE READINGS OUT SOME MINIMUM AMOUNT OF TIME
                min_interval = config.getint("MID","min_reading_interval_seconds")
                readingDuration = datetime.datetime.now() - readingStartTime
                if readingDuration.seconds < min_interval:
                    logging.info("taking a break for " + str(min_interval - readingDuration.seconds) + " seconds...")
                    time.sleep(min_interval - readingDuration.seconds)
                else:
                    logging.error("Unable to keep up with requested reading interval.  Last reading took "+str(readingDuration.seconds)+" > "+str(min_interval)+".")
                # END READING SPACING SLEEPY TIME
                # ##################################################
        except Exception as e:
            logging.critical("shit! encountered an unanticipated error."+str(e))
            logging.critical(traceback.format_exc())

def writeLatestWWWcfg(WWWcfg):
    f = open(LAST_WWW_CONFIG_LOC,"wb")
    cPickle.dump(WWWcfg,f)

def readLatestWWWcfg():
    f = open(LAST_WWW_CONFIG_LOC,"rb")
    return cPickle.load(f)
