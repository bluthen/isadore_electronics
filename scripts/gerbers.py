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

def usage():
	print >> sys.stderr, "Usage: "+sys.argv[0]+" {gerbers_prefix} {wanted_prefix}"
	print >> sys.stderr, "  -h, --help        Show this screen"

try:
	opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
	print opts
	print args
except getopt.GetoptError, err:
	print >> sys.stderr, str(err)
	usage()
	sys.exit(2)

if len(opts) > 0:
	options, optionsArgs = zip(*opts)
	if "-h" in options or "--help" in options:
		usage()
		sys.exit(2)



if len(args) != 2:
	usage()
	sys.exit(2)

gprefix = args[0]
wanted = args[1]

for ext in ['GBL', 'GBO', 'GBS', 'GTL', 'GTO', 'GTP', 'GTS', 'DRL']:
	os.system('mv '+gprefix+'.'+ext+' '+wanted+'.'+ext)
	os.system('zip '+wanted+'.zip '+wanted+'.'+ext)
	os.system('rm '+wanted+'.'+ext)

