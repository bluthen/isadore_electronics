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
import logging

def sortCommands(allCmds):
    cmdDict = dict()
    for cmd in allCmds:
        logging.debug(cmd)
        for bi,bn in enumerate(cmd.binName):
            if bn not in cmdDict:
                cmdDict[bn] = dict()
            if cmd.binSectionName[bi] not in cmdDict[bn]:
                cmdDict[bn][cmd.binSectionName[bi]] = ""
            cmdDict[bn][cmd.binSectionName[bi]]+=cmd.toASCII(bi)+"\n"
    return cmdDict

def printASCIIbinNameHeader(binName):
    print binName + "\n================"

def printASCIIbinSectionNameHeader(binSectionName):
    print "\t" + binSectionName + "\n================"

def printASCII(allCmds,lastReadingDT,lastWWWDT,lastUploadDT):
    # print some important date/time information
    print "Last reading occured: " + str(lastReadingDT)
    print "Last WWW config from WWW occured: " + str(lastWWWDT)
    print "Last upload occured: " + str(lastUploadDT)
    # print commands sorted by bin, then by bin section
    cmdDict = sortCommands(allCmds)
    for binName in cmdDict.iterkeys():
        printASCIIbinNameHeader(binName)
        for binSectionName in cmdDict[binName].iterkeys():
            printASCIIbinSectionNameHeader(binSectionName)
            # for cmd in cmdDict[binName][binSectionName]:
            #     print cmd
            print cmdDict[binName][binSectionName]

# def makeJSON(allCmds,config,lastReadingDT,lastWWWDT,lastUploadDT):
#     configDict = {"bins":None,"binSections":None,"lastReadingDT":None,"lastWWWDT":None,"lastUploadDT":None}
#     sensorDict = {}
#     cmdDict = sortCommands(allCmds)
#     for bin in cmdDict
    
#     return(configDict,sensorDict)

def newSensorItem(binNum,sectionNum,value):
    return {"bin":None,"section":None,"val":None}

