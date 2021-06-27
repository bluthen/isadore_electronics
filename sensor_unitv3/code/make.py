#!/usr/bin/python
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


import getopt
import sys
import os
import subprocess

micro=None

def usage():
	print >> sys.stderr, "Usage: "+sys.argv[0]+" [OPTIONS] ADDRESS"
	print >> sys.stderr, "  -h, --help                      Show this screen"
	print >> sys.stderr, "  -d, --debug                     Debug build"
	print >> sys.stderr, "  -p, --program                   Program unit"
	print >> sys.stderr, "  -c, --clean                     Clean"
	print >> sys.stderr, "  -f, --fuse                      Set fuse"
	print >> sys.stderr, "  --prev303                       Build for prev3.03 unit"
	print >> sys.stderr, "  --with-th                       Build with temperature humidty"
	print >> sys.stderr, "  --with-pressurev1=m,b           Build in v1 pressure module"
	print >> sys.stderr, "  --with-pressurev4a=cal_adjust   Build in v4a pressure module"
	print >> sys.stderr, "  --with-pressurev4b=cal_adjust   Build in v4b pressure module"
	print >> sys.stderr, "  --with-pressurev5=m,b           Build in v5 pressure module"
	print >> sys.stderr, "  --with-anemometer               Build in Anemometer module"
	print >> sys.stderr, "  --with-anemometerv2             Build in Anemometer module"
	print >> sys.stderr, "  --with-thermo                   Build in thermocouple module"
	print >> sys.stderr, "  --with-multit                   Build in Multipoint-temp module"
	print >> sys.stderr, "  --with-tach                     Build in tachometer module"

def setFuse():
	global micro
	subprocess.check_call('FMICRO='+micro[0]+' sh ./fuse_crystal_clock.sh', shell=True)


try:
	opts, args = getopt.getopt(sys.argv[1:], "hdpcf", ["help", "debug", "program", "clean", "fuse", "with-th", "with-pressure=", "with-pressurev1=", "with-pressurev4a=", "with-pressurev4b=", "with-pressurev5=", "with-anemometer", "with-anemometerv2", "with-thermo", "with-multit", "with-tach", "prev303"])
	print opts
	print args
except getopt.GetoptError, err:
	print >> sys.stderr, str(err)
	usage()
	sys.exit(2)

if len(opts) == 0 or len(args) > 1:
	usage()
	sys.exit(2)

options, optionsArgs = zip(*opts)

if "-h" in options:
	usage()
	sys.exit(1)

unitAddress = None 
try:
	unitAddress = int(args[0])
except:
	pass

micro = ['m328p', 'atmega328p']
if '--prev303' in options:
	micro=['m88', 'atmega88']

if "-f" in options or "--fuse" in options:
	setFuse()
	if not unitAddress:
		sys.exit(1)

if not unitAddress:
	print >> sys.stderr, "ERROR: No unit address." 
	usage()
	sys.exit(1)

UNITSRC=[]
UNITDEFS=["-DUNITADDR="+str(unitAddress)]

if '-d' in options or '--debug' in options:
	UNITSRC.append("./softuart.c")
	UNITDEFS.append("-DDEBUG")

if "--with-th" in options:
	UNITSRC.append("./modules/sht75.c")
	UNITDEFS.append("-DMODULE_TH")

if "--with-pressurev4a" in options:
	cal_pressure_adjust = optionsArgs[options.index("--with-pressurev4a")]
	pressureSrc=["./modules/pressurev4a/bmp180.c", "./modules/i2cmaster/twimaster.c", "./modules/pressurev4a/pressure.c"]
	UNITSRC.extend(pressureSrc)
	UNITDEFS.append("-DMODULE_PRESSUREV4A")
	UNITDEFS.append("-DCAL_PRESSUREV4A_ADJUST="+cal_pressure_adjust)

if "--with-pressurev4b" in options:
	cal_pressure_adjust = optionsArgs[options.index("--with-pressurev4b")]
	pressureSrc=["./modules/pressurev4b/BME280_driver/bme280.c", "./modules/i2cmaster/twimaster.c", "./modules/pressurev4b/pressure.c"]
	UNITSRC.extend(pressureSrc)
	UNITDEFS.append("-DMODULE_PRESSUREV4B")
	UNITDEFS.append("-DCAL_PRESSUREV4B_ADJUST_P="+cal_pressure_adjust)
	UNITDEFS.append("-DCAL_PRESSUREV4B_ADJUST_T=0")
	UNITDEFS.append("-DCAL_PRESSUREV4B_ADJUST_RH=0")

if "--with-pressurev1" in options:
	cal_pressure_adjust = optionsArgs[options.index("--with-pressurev1")].split(",")
	pressureSrc=["./modules/adc.c", "./modules/pressurev1/pressurev1.c"]
	UNITSRC.extend(pressureSrc)
	UNITDEFS.append("-DMODULE_PRESSUREV1")
	UNITDEFS.append("-DCAL_PRESSUREV1_M="+cal_pressure_adjust[0])
	UNITDEFS.append("-DCAL_PRESSUREV1_B="+cal_pressure_adjust[1])

if "--with-pressurev5" in options:
	cal_pressure_adjust = optionsArgs[options.index("--with-pressurev5")].split(",")
	pressureSrc=["./modules/adc.c", "./modules/pressurev5/pressurev5.c"]
	UNITSRC.extend(pressureSrc)
	UNITDEFS.append("-DMODULE_PRESSUREV5")
	UNITDEFS.append("-DCAL_PRESSUREV5_M="+cal_pressure_adjust[0])
	UNITDEFS.append("-DCAL_PRESSUREV5_B="+cal_pressure_adjust[1])

if "--with-anemometer" in options:
	UNITSRC.append("./modules/anemometer/anemometer.c")
	UNITDEFS.append("-DMODULE_ANEMOMETER")

if "--with-anemometerv2" in options:
	UNITSRC.append("./modules/anemometerv2/anemometer.c")
	UNITDEFS.append("-DMODULE_ANEMOMETERV2")

if "--with-thermo" in options:
	UNITSRC.append("./modules/thermocouplev2/thermocouple.c")
	UNITDEFS.append("-DMODULE_THERMOCOUPLE")

if "--with-multit" in options:
	multiSrc=["./modules/i2cmaster/twimaster.c", "./modules/multitemp/ds2482s.c", "./modules/multitemp/ds2482s_ds18b20.c", "./modules/multitemp/multitemp.c"]
	UNITSRC.extend(multiSrc)
	UNITDEFS.append("-DMODULE_MULTITEMP")

if "--with-tach" in options:
	UNITSRC.append("./modules/tachometer.c")
	UNITDEFS.append("-DMODULE_TACHOMETER")

if len(UNITSRC) == 0:
	print >> sys.stderr, "ERROR: No features used."
	usage()
	sys.exit(1)

makeOpts = ''
if '-p' in options or '--program' in options:
	makeOpts += 'program'

if '-c' in options or '--clean' in options:
	makeOpts += "clean"


envVars = 'UNITDEFS="' + (' '.join(UNITDEFS)) + '" UNITSRC="' + (' '.join(UNITSRC)) + '" MCU="'+micro[1]+'"'
print envVars
os.system(envVars+' make clean')
if makeOpts != "clean":
	os.system(envVars+' make '+makeOpts)

