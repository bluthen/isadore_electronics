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

#TODO: don't be so stupid and use dictionaries instead of all these list indexes!!
import matplotlib
# matplotlib.use('Agg')

import getopt
import csv
import numpy
import sys
import time
import traceback
import midsim
import StringIO
import datetime
import pylab
from matplotlib.backends.backend_pdf import PdfPages


def usage(p):
    if not p:
        p = sys.stderr
    print >> p, "Usage: " + sys.argv[0] + " [OPTION]..."
    print >> p, "  -h, --help             show this screen"
    print >> p, "  -v, --verbose          output verbose debug output"
    print >> p, "  -p t,c                 override default pulling samples every t seconds, c many times,"
    print >> p, "                         default is 0,300"
    print >> p, "  -r IPHOST;rp1:ra1      The port:address of the unit to use as pressure reference IPHOST; is optional"
    print >> p, "  -a IPHOST;p1:a1,IPHOST;p2:a2,...     The list of unit IPHOST port:adress to calibrate "
    print >> p, "                                       IPHOST; is optional if missing assumes local mid"
    print >> p, "                                       Examples:"
    print >> p, "                                       -a 1:4602,3:5492,172.16.43.22:3201;1:9873"
    print >> p, "  -n                     Bypass statistical safeguard checks, in step3"
    print >> p, "  --step0                Only do step0"
    print >> p, "  --step1=fileout        Only do step1 put output in 'fileout'"
    print >> p, "  --step2=filein,fileout Only do step2 using output from step1"
    print >> p, "  --step3=filein         Only do step3 using output from step2"
    print >> p, "  --verify               Only do verifying step"
    print >> p, ""
    print >> p, "-------------------------------------------------"
    print >> p, "By default it goes through these steps:"
    print >> p, " STEP0: Zero out calibration settings"
    print >> p, " STEP1: Gather data"
    print >> p, " STEP2: Calculate offset from data"
    print >> p, " STEP3: Program units with new calculated offsets, correctly adjusts finding current offset"
    print >> p, " VERIFY: Sample data gain verify offsets are valid, generate reports"
    print >> p, ""


def parse_unit_args(arg):
    pargs = [[[d for d in b.rsplit(':')] for b in c.rsplit(";")] for c in arg.split(",")]
    try:
        for i in range(len(pargs)):
            a = pargs[i]
            if len(a) > 1:
                a[0] = ':'.join(a[0])
            else:
                a.insert(0, None)
            pargs[i] = [a[0], int(a[1][0]), int(a[1][1])]
    except:
        print >> sys.stderr, 'ERROR: Unit argument is: IPHOST;PORT:ADDRESS or PORT:Address Examples seperated by commas'
        print >> sys.stderr, '   172.16.43.16:5200;1:3234,172.16.43.16:5200;1:3235  \n' \
                             '     or \n' \
                             '   1:3234,1:3235\n' \
                             'You can mixe IPHOST with non-IPHOST.'
        raise
    return pargs


def main():
    stats_threshold = [27, 1500, 24]  # [Error stddev, pre cal allowed error, post cal allowed error]
    config = {"verbose": False, "delay": 0, "counts": 300, "ref": [], "units": [], "stats_check": True, "step0": False,
              "step1": [None, None], "step2": [None, None], "step3": [None, None], "verify": False,
              "stats_threshold": stats_threshold}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvp:r:a:n",
                                   ["help", "verbose", "step0", "step1=", "step2=", "step3=", "verify"])
    except getopt.GetoptError, err:
        print str(err)
        usage(None)
        sys.exit(1)
    try:
        for o, a in opts:
            # print o, a
            if o in ("-h", "--help"):
                usage(sys.stdout)
                sys.exit(0)
            elif o in ("-v", "--verbose"):
                config["verbose"] = True
            elif o in ("-p",):
                a = [int(a) for a in a.split(",")]
                config["delay"] = a[0]
                config["counts"] = a[1]
            elif o in ("-r",):
                config["ref"] = parse_unit_args(a)[0]
            elif o in ("-a",):
                config["units"] = parse_unit_args(a)
            elif o in ("-n",):
                config["stats_check"] = False
            elif o in ("--step0",):
                config["step0"] = True
            elif o in ("--step1",):
                config["step1"][1] = a
            elif o in ("--step2",):
                config["step2"] = a.split(",")
                config["step2"][0] = parse_step2in(config["step2"][0])
            elif o in ("--step3",):
                config["step3"] = a.split(",")
                config["step3"][0] = parse_step3in(config["step3"][0])
            elif o in ("--verify",):
                config["verify"] = True
    except SystemExit as e:
        sys.exit(e)
    except:
        print >> sys.stderr, 'ERROR: Invalid option argument.'
        print >> sys.stderr, traceback.format_exc()
        print >> sys.stderr
        usage(None)
        sys.exit(13)

    if len(config["units"]) == 0:
        print >> sys.stderr, "ERROR: No units provided with -a"
        usage(None)
        sys.exit(11)

    if len(config["ref"]) != 3:
        print >> sys.stderr, "ERROR: Missing reference information -r"
        usage(None)
        sys.exit(12)

    # Lets start
    if config["verify"]:
        step4(config)
    elif config["step3"][0]:
        step3(config)
    elif config["step2"][0]:
        step2(config)
    elif config["step1"][1]:
        step1(config)
    elif config["step0"]:
        step0(config)
    else:
        step0(config)
        step1(config)
        step2(config)
        step3(config)
        step4(config)
        sys.exit(0)


def set_cal(hostipport, port, address, value):
    outstream = StringIO.StringIO()
    remote = ""
    if hostipport:
        remote = "-r "+hostipport
    args = (
        "%s %s -f csv -p %d -a %d -t %s --set-cal=%d" % ("midsim.py", remote, port, address, "pressurewide", value)
    ).split()
    midsim.midsim(args, outstream)
    mout = outstream.getvalue()
    outstream.close()
    v = int(mout.rstrip().split(",")[1])
    if v != value:
        print >> sys.stderr, "ERROR: Unit calibration was not set correctly: sp = %d != pv = %d" % (value, v)
        sys.exit(7)


def step0(config):
    print "Zeroing out calibration settings..."
    for unit in config["units"]:
        hostipport = unit[0]
        port = unit[1]
        address = unit[2]
        set_cal(hostipport, port, address, 0)


def step1_diffport(config):
    # [[Port, Unit_ADDRESS, REF_VALUE, UNIT_VALUE, REF_VALUE], ...]
    alldata = []
    for i in xrange(config["counts"]):
        sys.stdout.write("Sample %d/%d                  \r" % (i + 1, config["counts"]))
        sys.stdout.flush()
        for unit in config["units"]:
            # Get Reference value
            data = []
            data.extend([unit[0], unit[1], unit[2]])

            if unit[0] is config["ref"][0] and unit[1] == config["ref"][1]:
                outstream = StringIO.StringIO()
                remote = ""
                if unit[0]:
                    remote = "-r "+unit[0]
                midsim.midsim(["midsim.py"] + ("%s -f csv -p %d -a %d,%d,%d -t %s" % (
                    remote, config["ref"][1], config["ref"][2], unit[2], config["ref"][2], "pressurewide")).split(),
                    outstream)
                mout = outstream.getvalue()
                outstream.close()
                data.extend([int(c) for c in mout.rstrip().split(",")[1:]])
                alldata.append(data)
            else:
                outstream = StringIO.StringIO()
                remote = ""
                if config["ref"][0]:
                    remote = "-r "+config["ref"][0]
                midsim.midsim(("%s %s -f csv -p %d -a %d -t %s" % (
                    "midsim.py", remote, config["ref"][1], config["ref"][2], "pressurewide")).split(), outstream)
                mout = outstream.getvalue()
                outstream.close()
                data.append(int(mout.rstrip().split(",")[1]))

                # Get other unit values
                outstream = StringIO.StringIO()
                remote = ""
                if unit[0]:
                    remote = "-r "+unit[0]
                args = "%s %s -f csv -p %d -a %d -t %s" % ("midsim.py", remote, unit[1], unit[2], "pressurewide")
                args = args.split()
                midsim.midsim(args, outstream)
                mout = outstream.getvalue()
                outstream.close()
                data.append(int(mout.rstrip().split(",")[1]))

                # Get Reference value
                outstream = StringIO.StringIO()
                remote = ""
                if config["ref"][0]:
                    remote = "-r "+config["ref"][0]
                args = "%s %s -f csv -p %d -a %d -t %s" % (
                    "midsim.py", remote, config["ref"][1], config["ref"][2], "pressurewide")
                args = args.split()
                midsim.midsim(args, outstream)
                mout = outstream.getvalue()
                outstream.close()
                data.append(int(mout.rstrip().split(",")[1]))
                alldata.append(data)
        time.sleep(config["delay"])
    print
    return alldata


def step1(config):
    # Gather Data
    print "Gathering Samples..."

    sameports = True
    port = config["units"][0][1]
    for unit in config["units"]:
        if unit[0] is not config["units"][0][0] or unit[1] != port:
            sameports = False
            break

    if sameports and (config["ref"][0] is not config["units"][0][0] or config["ref"][1] != port):
        sameports = False

    # [[Port, Unit_ADDRESS, REF_VALUE, UNIT_VALUE, REF_VALUE], ...]
    if sameports:
        # XXX: Make a super fast sampler
        alldata = step1_diffport(config)
    else:
        alldata = step1_diffport(config)
    if config["step1"][1] is not None:
        with open(config["step1"][1], 'wb') as f:
            for row in alldata:
                f.write("%s,%d,%d,%d,%d,%d\n" % (row[0], row[1], row[2], row[3], row[4], row[5]))
        sys.exit(0)
    else:
        config["step2"][0] = alldata


def parse_step2in(filename):
    with open(filename, 'rb') as f:
        sr = csv.reader(f, delimiter=',', quotechar='"')
        alldata = []
        for row in sr:
            d = [row[0], int(row[1]), int(row[2]), int(row[3]), int(row[4]), int(row[5])]
            if d[0] == 'None':
                d[0] = None
            alldata.append(d)
        return alldata


def step2(config):
    print "Calculating States..."
    # sort step2 in data
    # [[port, address, [[r1, v1, r2], ...]]]
    sorted_data = []
    for row in config["step2"][0]:
        found = False
        for srow in sorted_data:
            if srow[0] is row[0] and srow[1] == row[1] and srow[2] == row[2]:
                srow[3].append([row[3], row[4], row[5]])
                found = True
                break
        if not found:
            sorted_data.append([row[0], row[1], row[2], [[row[3], row[4], row[5]]]])

    # Calculate Offsets
    # [ [port, address, mean_error, stddev_error, minerror, maxerror, suggested_offset] ]
    calculations = []
    for row in sorted_data:
        zdata = zip(*row[3])
        r = (numpy.array(zdata[0]) + numpy.array(zdata[2])) / 2.0
        me = r - numpy.array(zdata[1])
        mean_error = numpy.mean(me)
        stddev_error = numpy.std(me)
        minerror = numpy.min(me)
        maxerror = numpy.max(me)
        suggested_offset = round(mean_error)
        calculations.append([row[0], row[1], row[2], mean_error, stddev_error, minerror, maxerror, suggested_offset])

    if config["step2"][1] is not None:
        with open(config["step2"][1], 'wb') as f:
            for row in calculations:
                f.write("%s,%d,%d,%f,%f,%f,%f,%d\n" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
        sys.exit(0)
    else:
        config["step3"][0] = calculations


def parse_step3in(filename):
    with open(filename, 'rb') as f:
        sr = csv.reader(f, delimiter=',', quotechar='"')
        alldata = []
        for row in sr:
            d = [row[0], int(row[1]), int(row[2]), float(row[3]), float(row[4]), float(row[5]), float(row[6]),
                 int(row[7])]
            if d[0] is 'None':
                d[0] = None
            alldata.append(d)
        return alldata


def get_cal(hostipport, port, address):
    outstream = StringIO.StringIO()
    remote = ""
    if hostipport:
        remote = "-r "+hostipport
    args = "%s %s -f csv -p %d -a %d -t %s --get-cal" % ("midsim.py", remote, port, address, "pressurewide")
    args = args.split()
    midsim.midsim(args, outstream)
    mout = outstream.getvalue()
    outstream.close()
    # real_offset = suggested_offset + current_offset
    return int(mout.rstrip().split(",")[1])


def step3(config):
    print "Gathering current calibration settings..."
    # [ [port, address, mean_error, stddev_error, minerror, maxerror, suggested_offset] ]
    # Get current calibration offsets for all units
    for unit in config['step3'][0]:
        hostipport = unit[0]
        port = unit[1]
        address = unit[2]
        cal = get_cal(hostipport, port, address)
        # real_offset = suggested_offset + current_offset
        unit.append(unit[7] + cal)
    if not config['stats_check']:
        print "Bypassing Checking stats."
    else:
        print "Checking Stats..."
        for unit in config['step3'][0]:
            if abs(unit[4]) > config["stats_threshold"][0]:
                print >> sys.stderr, "WARNING Std dev too high, %s;%d:%d, stdev: %f" % (
                    unit[0], unit[1], unit[2], unit[4])

    # Program the offsets
    print "Setting Calibration Values..."
    for unit in config['step3'][0]:
        if abs(unit[8]) > config["stats_threshold"][1]:
            print >> sys.stderr, "ERROR: Skipping, offset too large %s;%d:%d - %d" % (
                unit[0], unit[1], unit[2], unit[8])
            continue
        hostipport = unit[0]
        port = unit[1]
        address = unit[2]
        set_cal(hostipport, port, address, unit[8])


def step4_console_report(config):
    print "P-A: Status"
    for unit in config['step3'][0]:
        print "%s;%d-%d: " % (unit[0], unit[1], unit[2]),
        if abs(unit[4]) > config["stats_threshold"][0]:
            print "Error stdev %d > %d" % (unit[4], config["stats_threshold"][0])
        elif abs(unit[7]) > config["stats_threshold"][2]:
            print "Error too large abs(%f) > %d" % (unit[7], config["stats_threshold"][2])
        else:
            print "OK %f" % (unit[3],)


def step4_pdf_report(config):
    # [[port, address, [[r1, v1, r2], ...]]]
    sorted_data = []
    for row in config["step2"][0]:
        found = False
        for srow in sorted_data:
            if srow[0] is srow[0] and srow[1] == row[1] and srow[2] == row[2]:
                srow[3].append([row[2], row[3], row[4]])
                found = True
                break
        if not found:
            sorted_data.append([row[0], row[1], row[2], [[row[3], row[4], row[5]]]])

    report_name = 'pressure_cal_' + datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f") + ".pdf"

    print "Generating PDF Report: " + report_name
    with PdfPages(report_name) as pdf:
        i = 0
        for row in sorted_data:
            i += 1
            if i % 5 == 0:
                pdf.savefig()
                pylab.close()
                i = 1

            zdata = zip(*row[3])
            r = (numpy.array(zdata[0]) + numpy.array(zdata[2])) / 2.0
            errors = r - numpy.array(zdata[1])

            mu = numpy.mean(errors)
            sigma = numpy.std(errors)

            # print "n=%d, mu=%f, sigma=%f" % (len(errors), mu, sigma)

            pylab.subplot(2, 2, i)
            n, bins, patches = pylab.hist(errors, 50, normed=1, histtype='stepfilled')
            # print "%d:%d - %f, %f" % (row[0], row[1], mu, sigma)

            if abs(sigma) > config["stats_threshold"][0]:
                status = 'FAILED sigma > %d' % (config["stats_threshold"][0],)
            elif abs(mu) > config["stats_threshold"][2]:
                status = 'FAILED mu > %d' % (config["stats_threshold"][2],)
            else:
                status = "PASS"

            pylab.setp(patches, 'facecolor', 'g', 'alpha', 0.75)
            pylab.title("%s;%d:%d\nn=%d, mu=%.1f, sig=%.1f\n%s" % (
                row[0], row[1], row[2], len(errors), mu, sigma, status))
            y = pylab.normpdf(bins, mu, sigma)
            l = pylab.plot(bins, y, 'k--', linewidth=1.5)
        pylab.close()
        d = pdf.infodict()
        d['Title'] = 'Pressure Calibration'
        d['Author'] = u'Exoteric Analytics Calibrator'
        d['CreationDate'] = datetime.datetime.today()
        d['ModDate'] = datetime.datetime.today()


def step4_csv_report(config):
    report_name = 'pressure_cal_' + datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f") + ".csv"
    with open(report_name, 'wb') as f:
        f.write('"host","port","address","status","status_reason","cal_offset","mu","sigma"\n')
        for unit in config['step3'][0]:
            hostipport = unit[0]
            port = unit[1]
            address = unit[2]
            sigma = unit[4]
            mu = unit[7]
            cal = get_cal(hostipport, port, address)
            if abs(sigma) > config["stats_threshold"][0]:
                status = 'FAILED'
                reason = 'sigma > %d' % (config["stats_threshold"][0],)
            elif abs(mu) > config["stats_threshold"][2]:
                status = 'FAILED'
                reason = 'mu > %d' % (config["stats_threshold"][2],)
            else:
                status = "PASS"
                reason = ""
            f.write('%s,%d,%d,"%s","%s",%d,%.1f,%.1f\n' % (hostipport, port, address, status, reason, cal, mu, sigma))


def step4(config):
    # STEP4: Verify offsets are good
    print "Verifying Calibration..."
    config["step1"] = [None, None]
    config["step2"] = [None, None]
    # Regather data
    step1(config)
    # Regather stats
    step2(config)

    # Console report
    step4_console_report(config)
    # CSV Report
    step4_csv_report(config)

# PDF Report
# step4PDFReport(config)

if __name__ == "__main__":
    main()
