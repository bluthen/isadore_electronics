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


"""
The idea here is we have two pressure sensors, address 100 and 101.

We then take four consective readings: 100, 101, 100, 100

I took 600 of the four consective readings 1 second part.

The reason for two 100 readings at the end is so we can remove time pressure change error.

In our leaky pressure chamber the time between two consective readings the pressure will change.

The time between the first 100, 101 reading the pressure will be different for the 101 than it was for the 100.

So to get the difference in pressure that time made I subtract the later 100's by each other and can apply it to the 100 and 101 reading.
"""




import csv
import datetime
import matplotlib.pyplot as pyplot
import numpy

doPlots = True


def readData(filename):
	icdata = []
	with open(filename, 'rb') as f:
		sr = csv.reader(f, delimiter=',', quotechar='"')
		for row in sr:
			r=[]
			r.append(datetime.datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S.%f"))
			for i in xrange(1, len(row)):
				r.append(float(row[i]))
			icdata.append(r)
	return zip(*icdata)

def computeStats(data):
	b = {}
	if len(data) >= 3:
		#noise+time_error+sensor_error
		b['ntse'] = numpy.array(data[1]) - numpy.array(data[2])
		b['ntse_mean'] = numpy.mean(b['ntse'])
		b['ntse_std'] = numpy.std(b['ntse'])
		b['ntse_min'] = numpy.min(b['ntse'])
		b['ntse_max'] = numpy.max(b['ntse'])
	if len(data) == 5:
		#noise+time_error
		b['nte'] = numpy.array(data[3]) - numpy.array(data[4])
		b['nte_mean'] = numpy.mean(b['nte'])
		b['nte_std'] = numpy.std(b['nte'])
		b['nte_min'] = numpy.min(b['nte'])
		b['nte_max'] = numpy.max(b['nte'])
	return b

def printStats(title, statData, origData):
	print "==== %s ====" % (title)
	if len(origData) == 5:
		print "noise+time_error"
		print "  %s:\t%f" % ('mean', statData['nte_mean'])
		print "  %s:\t%f" % ('std', statData['nte_std'])
		print "  %s:\t%f" % ('min', statData['nte_min'])
		print "  %s:\t%f" % ('max', statData['nte_max'])
	print "noise+time_error+sensor_error"
	print "  %s:\t%f" % ('mean', statData['ntse_mean'])
	print "  %s:\t%f" % ('std', statData['ntse_std'])
	print "  %s:\t%f" % ('min', statData['ntse_min'])
	print "  %s:\t%f" % ('max', statData['ntse_max'])
	if doPlots:
		p1, = pyplot.plot(origData[0], origData[1], 'b-')
		p2, = pyplot.plot(origData[0], origData[2], 'r-')
		pyplot.legend([p1, p2], ['1', '2'])
		pyplot.title(title+': adr100 and adr101')
		pyplot.show()

		pyplot.plot(origData[0], statData['ntse'], '-')
		pyplot.title(title+': noise+time_error+sensor_error')
		pyplot.show()

		if len(origData) == 5:
			pyplot.plot(origData[0], statData['nte'], '-')
			pyplot.title(title+': noise+time_error')
			pyplot.show()


#Pretty stable pressure (environmental pressure)
calDataA = readData('initialcal.csv')
calDataB = computeStats(calDataA)
printStats('Initial CAL', calDataB, calDataA)

# Inside chamber
calChDataA = readData('initialcal_chamber.csv')
calChDataB = computeStats(calChDataA)
printStats('Initial Chamber CAL', calChDataB, calChDataA)

#Inside chamber but seeing if querier one sensor a lot causes heat effects
calCh2DataA = readData('initialcal_chamber_two.csv')
calCh2DataB = computeStats(calCh2DataA)
printStats('Initial Chamber No Time CAL', calCh2DataB, calCh2DataA)


#Inside chamber with a bunch different pressures
calPDataA = readData('chamber_pressure.csv')
calPDataB = computeStats(calPDataA)
printStats('Initial Pressure CAL', calPDataB, calPDataA)




# See how well a fit just having a bias does with stable pressure.
adjCalData = numpy.copy(calDataA)
adjCalData[2] = adjCalData[2] + float(calDataB['ntse_mean'])
adjCalDataStat = computeStats(adjCalData)
printStats('Adjusted Initial CAL', adjCalDataStat, adjCalData)


# See how well the bias works at various pressures
# We also subtract time error, as the pressure chamber leaks a lot that the pressure is different between two consective readings.
adjPData = numpy.copy(calPDataA)
#Remove sensor error, and time error
adjPData[2] = adjPData[2] + float(calDataB['ntse_mean'])
adjPData[2] = adjPData[2] + calPDataB['nte']
adjPDataStat = computeStats(adjPData)
printStats('Adjusted Pressure CAL', adjPDataStat, adjPData)



