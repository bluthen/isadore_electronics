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

import pylab
import numpy
import csv
import math
import time
from matplotlib.backends.backend_pdf import PdfPages


#Load data
alldata = []
with open("step1.csv", 'rb') as f:
	sr = csv.reader(f, delimiter=',', quotechar='"')
	alldata = []
	for row in sr:
		d = [int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4])]
		alldata.append(d)


#[[port, address, [[r1, v1, r2], ...]]]
sortedData = []
for row in alldata:
	found = False
	for srow in sortedData:
		if srow[0] == row[0] and srow[1] == row[1]:
			srow[2].append([row[2], row[3], row[4]])
			found = True
			break
	if not found:
		sortedData.append([row[0], row[1], [[row[2], row[3], row[4]]]])


with PdfPages('multipage_pdf.pdf') as pdf:
	i = 0
	for row in sortedData:
		i=i+1
		if(i % 5 == 0):
			pdf.savefig()
			pylab.close()
			i = 1

		zdata = zip(*row[2])
		r = (numpy.array(zdata[0]) + numpy.array(zdata[2]))/2.0
		errors = r - numpy.array(zdata[1])

		mu = numpy.mean(errors)
		sigma = numpy.std(errors)

		pylab.subplot( 2, 2, i)
		n, bins, patches = pylab.hist(errors, 50, normed=1, histtype='stepfilled')
		print "%d:%d - %f, %f" % (row[0], row[1], mu, sigma)

		#pylab.setp(patches, 'facecolor', 'g', 'alpha', 0.75)
		pylab.title("%d:%d" % (row[0], row[1]))
		y = pylab.normpdf( bins, mu, sigma)
		l = pylab.plot(bins, y, 'k--', linewidth=1.5);
		if(row[1] == 1981):
			print errors
			print bins
			print y
			print n
	pdf.savefig()
	pylab.close();
	time.sleep(5)

