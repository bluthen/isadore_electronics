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
import hubComm
import hubPackets
from hubPackets import HubTempHumCmd,HubPressureWideCmd,MultiTResetCmd
# 3rd party modules
import serialComm
# std lib modules
import logging
import ConfigParser
import time
import os
import sys
import datetime
import getopt
import traceback

CONFIG_LOC = '../MID.cfg'
SHT = "SHT"
MPT = "MPT"
KPA = "KPA"
TC = "T_C"
SENSOR_TYPES = (SHT,MPT,KPA,TC)

def parseInfile(fh):
    units = {}
    for st in SENSOR_TYPES:
        units[st] = []
    for line in fh:
        port,stype,midname,addy = line.split(":")
        units[stype] += [(int(port),int(addy),midname)]
    return units

def testCmd(cmd):
    if isinstance(cmd,HubTempHumCmd):
        return cmd.tempRaw[0] != 0
    if isinstance(cmd,HubPressureWideCmd):
        return cmd.raw[0] != 0
    if isinstance(cmd,MultiTResetCmd):
        return cmd.replies[0] != 0

def usage(p):
    if(not p):
        p = sys.stderr
    print >> p, "Usage: "+sys.argv[0]+" [OPTION]..."
    print >> p, "  -h, --help             show this screen"
    # print >> p, "  -v, --verbose          output verbose debug output"
    print >> p, "  -f infile              file containing list of port/address pairs"
    # print >> p, "  -o reportfile          Write report to reportfile as well as stdout"
    print >> p, "  -c c1,c2,c3...         restrict to chains listed"

if __name__ == "__main__":
    ports = (1,2,3,4,5,6)
    # 
    # load configuration
    # 
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_LOC)
    # 
    # parse arguments
    # 
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hn:f:c:", ["help", "verbose"])
    except getopt.GetoptError, err:
        print str(err)
        usage(None)
        sys.exit(1)
    try:
        for o, a in opts:
            if o in ("-h", "--help"):
                usage(sys.stdout)
                sys.exit(0)
            elif o in ("-c"):
                ports=[int(a) for a in a.split(",")]
            elif o in ("-f"):
                infilePath = a
    except SystemExit as e:
        sys.exit(e)
    except:
        print >> sys.stderr, 'ERROR: Invalid option argument.'
        print >> sys.stderr, traceback.format_exc()
        print >> sys.stderr
        usage(None)
        sys.exit(13)
    # 
    # get list of units, in chain order, from a file path supplied as argument
    # 
    infile_fh = open(infilePath)
    units = parseInfile(infile_fh)
    infile_fh.close()
    # 
    # create connection to hub
    # 
    if("hub_serial" in zip(*config.items('MID'))[0]):
        hubCon = hubComm.HubComm(serialPath=config.get("MID", "HUB_SERIAL"))
    else:
        hubCon = hubComm.HubComm(config.get("MID","MID_IP"),
                                 config.getint("MID","MID_PORT"),
                                 config.get("MID","HUB_IP"),
                                 config.getint("MID","HUB_PORT"))
    # 
    # create SHT commands
    # 
    hubCmds = []
    hubCmds_types = []
    for unit in units[SHT]:
        if unit[0] in ports:
            hubCmds += [HubTempHumCmd(sensorID=[0],
                                      port=unit[0],
                                      addy=[unit[1]],
                                      convertPy=[("x","x")],
                                      bias=[(0,0)])]
            hubCmds_types += [SHT]
    for unit in units[KPA]:
        if unit[0] in ports:
            hubCmds += [HubPressureWideCmd(sensorID=[0],
                                           port=unit[0],
                                           addy=[unit[1]],
                                           convertPy=["x"],
                                           bias=[0])]
            hubCmds_types += [KPA]
    for unit in units[MPT]:
        if unit[0] in ports:
            hubCmds += [MultiTResetCmd(port=unit[0],
                                       addy=[unit[1]])]
            hubCmds_types += [MPT]
    # 
    # process each command
    # 
    allErrs = []
    for cmd,cmd_t in zip(hubCmds,hubCmds_types):
        allErrs += [hubCon.processCommand(cmd)]
        if testCmd(cmd):
            print cmd.port,cmd.addy,cmd_t,"good"
        else:        
            print cmd.port,cmd.addy,cmd_t,"bad"
