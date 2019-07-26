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
import os
import datetime
import csv
import sys
import time
import traceback
import midsim
import StringIO

#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

def usage(p):
	if(not p):
		p = sys.stderr
	print >> p, "Usage: "+sys.argv[0]+" [OPTION]..."
	print >> p, "  -h, --help             show this screen"
	print >> p, "  -v, --verbose          output verbose debug output"
	print >> p, "  -s t,c                 Query single unit at a time in batches of c < 32 with t "
	print >> p, "                         second between each"
	print >> p, "  -i t                   Query alternating in order given with t seconds between each"
	print >> p, "  -n s                   Minimum number of samples n per unit until done"
	print >> p, "  -t type                The type to query"
	print >> p, "  -f samplefile          Write out samples to samplefile, instead of just keeping in memory"
	print >> p, "  -o reportfile          Write report to reportfile as well as stdout"
	print >> p, "  -a p1:a1,...,pn:an     Query these units port:address"
        print >> p, "  -l filepath            read addresses from specified file"


def main():
	config = { "verbose": False, "delay": 0, "counts": 32, "alternate": False, "samples_per_unit": 300, "type": "temphum", "samplefile": None, "reportfile": 'reliability_'+datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f")+".csv", "units": [] }
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvs:i:n:t:f:o:a:l:", ["help", "verbose"])
	except getopt.GetoptError, err:
		print str(err)
		usage(None)
		sys.exit(1)
	try:
		for o, a in opts:
			#print o, a
			if o in ("-h", "--help"):
				usage(sys.stdout)
				sys.exit(0)
			elif o in ("-v", "--verbose"):
				config["verbose"] = True
			elif o in ("-s"):
				a=[int(a) for a in a.split(",")]
				config["delay"]=a[0]
				config["counts"]=a[1]
			elif o in ("-i"):
				config["alternate"] = True
				config["delay"]=int(a)
			elif o in ("-t"):
				config["type"] = a
			elif o in ("-a"):
				config["units"] = [[int(b) for b in c.split(":")] for c in a.split(",")]
			elif o in ("-l"):
				config["units"] = []
				with open(a) as f:
					for line in f:
						config["units"] += [[int(b) for b in line.split(":")]]
			elif o in ("-n"):
				config["samples_per_unit"] = int(a)
			elif o in ("-o"):
				config["reportfile"] = a
			elif o in ("-f"):
				config["samplefile"] = a
	except SystemExit as e:
		sys.exit(e)
	except:
		print >> sys.stderr, 'ERROR: Invalid option argument.'
		print >> sys.stderr, traceback.format_exc()
		print >> sys.stderr
		usage(None)
		sys.exit(13)
	
	if len(config["units"]) == 0:
		print >> sys.stderr, "ERROR: No units provided with -a or -l"
		usage(None)
		sys.exit(11)
	
	if config["counts"] > 32:
		print >> sys.stderr, "ERROR: -s count needs to be <= 32"
		usage(None)
		sys.exit(12)

	#Lets start
	step1(config)
	step2(config)
	step3(config)

def step1_sample(config):
	#[[Port, Unit_ADDRESS, VALUE1, VALUE2, ...], ...]
	alldata = []
	if not config["alternate"]:
		for unit in config["units"]:
			count = 0
			data = []
			data.extend([unit[0], unit[1]])
			while count < config["samples_per_unit"]:
				sys.stdout.write("Unit %d:%d Sample: %d/%d                  \r" % (unit[0], unit[1], count+1, config["samples_per_unit"]))
				sys.stdout.flush()
				#Get Reference value

				outstream = StringIO.StringIO()
				mstr="%s -f csv -t %s -p %d -a %d"+",%d"*(config["counts"]-1)
				mparm = ["midsim.py", config["type"], unit[0]]
				mparm.extend([unit[1]]*config["counts"])
				mparm = tuple(mparm)
				midsim.midsim((mstr % mparm).split(" "), outstream)
				mout = outstream.getvalue()
				outstream.close()
				d = mout.rstrip().split(",")[1:]
				data.extend(d)

				count = count+len(d)
				time.sleep(config["delay"])
			alldata.append(data)
		print
	return alldata



#sample
def step1(config):
	#Gather Data
	print "Gathering Samples..."

	alldata = step1_sample(config)
	#if config["samplefile"] != None:
	#	with open(config["samplefile"], 'wb') as f:
	#		for row in alldata:
	#			f.write("%d,%d,%d,%d,%d\n" % (row[0], row[1], row[2], row[3], row[4]))
	config["sampledata"] = alldata

#analyse
def step2(config):
	counts = []
	for row in config["sampledata"]:
		total = 0
		errors = 0
		for col in row[2:]:
			if col == '"ERR"':
				errors = errors+1
			total = total+1
		counts.append([str(row[0])+':'+str(row[1]), errors, total])
	config["stats"] = counts

#Report
def step3(config):
	print "Results..."
	f = open(config["reportfile"], 'wb')
	for row in config["stats"]:
		f.write("\"%s\",%d,%d\n" % (row[0], row[1], row[2]))
		print "%s: %d/%d=%.2f" % (row[0], row[1], row[2], float(row[1])/float(row[2]))
	f.close()

if __name__ == "__main__":
	main()
