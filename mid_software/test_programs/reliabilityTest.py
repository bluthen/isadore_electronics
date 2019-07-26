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
from hubPackets import HubTempHumCmd
# 3rd party modules
import serialComm
# std lib modules
import ConfigParser
import sys
import random
import getopt

import responseTest as rt

def usage(p):
	if(not p):
		p = sys.stderr
	print >> p, "Usage: "+sys.argv[0]+" [OPTION]..."
	print >> p, "  -h, --help             show this screen"
	# print >> p, "  -v, --verbose          output verbose debug output"
	print >> p, "  -n s                   number of samples per unit"
	print >> p, "  -f infile              file containing list of port/address pairs"
	# print >> p, "  -o reportfile          Write report to reportfile as well as stdout"
        print >> p, "  -c c1,c2,c3...         restrict to chains listed"

CONFIG_LOC = '../MID.cfg'

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
            elif o in ("-n"):
                numReads = int(a)
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
    # # 
    # # cmd line args
    # # 
    # # TODO: add an optional ports argument
    # infilePath = sys.argv[1]
    # numReads = int(sys.argv[2])
    # ports=(1,2,3,4,5,6)
    
    # 
    # get list of units, in chain order, from the supplied file path supplied
    # 
    # open it and get the list of units
    infile_fh = open(infilePath)
    units = rt.parseInfile(infile_fh)
    infile_fh.close()
    print units
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
    # for each unit, create a T/RH command for each time we should read from it
    # then, shuffle the list
    # finally, reduce to the ports specified in cmd line
    # TODO: only does SHT for now. fix this.
    # TODO: only do one type of sensor for each unit?
    # 
    hubCmds = []
    for unit in units[rt.SHT]:
        for nR in range(numReads):
            hubCmds += [HubTempHumCmd(sensorID=[0],
                                      port=unit[0],
                                      addy=[unit[1]],
                                      convertPy=[("x","x")],
                                      bias=[(0,0)])]
    random.shuffle(hubCmds)
    hubCmds = [hC for hC in hubCmds if hC.port in ports]
    # 
    # process each command
    # 
    # TODO: do cool screen update like Russ's reliability.py
    allErrs = []
    for cmdi,cmd in enumerate(hubCmds):
        allErrs += [hubCon.processCommand(cmd)]
        sys.stdout.write("Reading %d:%d Progress: %d/%d                  \r" % (cmd.port, cmd.addy[0], cmdi+1, len(hubCmds)))
        print
    # 
    # compute results
    # 
    results = []
    gen_units = (x for x in units[rt.SHT] if x[0] in ports)
    for unit in gen_units:
        unitCmds = [hC for hC in hubCmds if (hC.port==unit[0] and hC.addy[0]==unit[1])]
        goodCmds = [uC for uC in unitCmds if uC.tempRaw[0] != 0]
        print unit[0],":",unit[1],len(goodCmds),len(unitCmds),float(len(goodCmds))/float(len(unitCmds))
