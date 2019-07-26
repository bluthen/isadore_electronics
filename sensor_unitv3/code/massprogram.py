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
import readline
import os
import time

fail=True
address = 0
while(fail and address == 0):
	try:
		address = int(raw_input("Starting address: "))
		fail=False
	except:
		print "Bad Input."
		pass

print "First address, "+str(address)


while(True):
	print
	print "*******************************************************************************"
	print "1) Make sure the power is off."
	print "2) Insert a new chip."
	print "3) Turn on the power."
	print "4) Press enter."
	print 
	print "This chip will have address: "+str(address)
	print
	raw_input("Press <Enter> to begin programing the microcontroller: ")

	print "Cleaning."
	returnCode = -1
	while(returnCode != 0):
		returnCode = os.system("make clean")
		if(returnCode != 0):
			print "ERROR: Failed to clean."
			raw_input("Press <Enter> to try again.")

	time.sleep(1)
	cmd = "sh fuse_crystal_clock.sh"
	print "Setting Fuse Command: "+cmd
	returnCode = -1
	while(returnCode != 0):
		returnCode = os.system(cmd)
		if(returnCode != 0):
			print
			print "ERROR: Failed to set fuse bits."
			print "ERROR: 1) Make sure the microcontroller is properly inserted into the programmer."
			print "ERROR: 2) Make sure the power is on."
			print
			raw_input("Press <Enter> to try again.")

	cmd="make clean"
	print "Cleaning Command:"+cmd
	returnCode = -1
	while(returnCode != 0):
		returnCode = os.system(cmd)
		if(returnCode != 0):
			print "ERROR: Failed to clean."
			raw_input("Press <Enter> to try again.")
	time.sleep(1)

	cmd = "UNITDEFS=\"-DUNITADDR="+str(address)+" -DUNITFEATURES=3\" make program"
	print "Programming Command: "+cmd
	returnCode = -1
	while(returnCode != 0):
		returnCode = os.system(cmd)
		if(returnCode != 0):
			print
			print "ERROR: Failed to program the microcontroller."
			print "ERROR: Make sure the microcontroller is properly inserted into the programmer."
			print "ERROR: Make sure the power is on."
			print
			raw_input("Press <Enter> to try again.")

	time.sleep(1)
	print
	print
	print "The microcontroller has been properly programmed:"
	print "1) Turn the power off."
	print "2) Make sure the address label '"+str(address)+"' is on the microcontroller."
	print "3) Remove microcontroller from programmer and put it in the anti-static container."
	print
	raw_input("Press <Enter> to continue.")
	address=address+1

