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

# Simulates a MID to test ethernet board and hub

import serial
import socket
from StringIO import StringIO
import struct
import sys
import getopt
import time
import traceback
import random
import datetime
import os
import json
import requests
import logging
from flask import Flask, Response, request, abort

app = Flask(__name__)

@app.route('/midsim', methods=["GET"])
def flask_midsim_get():
    cmd = json.loads(request.args.get('cmd'))
    stderr = StringIO()
    stdout = StringIO()
    try:
        midsim(cmd, stdout, stderr)
    except:
        stderr.write(traceback.format_exc())
    ret = {'stdout': stdout.getvalue(), 'stderr': stderr.getvalue()}
    return Response(json.dumps(ret), mimetype='application/json')


def start_server(host, port):
    fh = logging.FileHandler('flash.log')
    fh.setLevel(logging.WARN)
    fh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    app.logger.addHandler(fh)
    app.run(host=host, port=port)


def server_query(hostport, argv, stdout, stderr):
    cmd = json.dumps(argv)
    req = requests.get('http://%s/midsim' % (hostport,), params={'cmd': cmd})
    if req.status_code < 200 or req.status_code >= 300:
        stderr.write('ERROR: server query(%d): %s' % (req.status_code, req.text))
    else:
        out = req.json()
        stdout.write(out['stdout'])
        stderr.write(out['stderr'])



def usage(p=sys.stderr):
    print >> p, "Usage: " + sys.argv[0] + " [OPTION]..."
    print >> p, "  -h, --help            show this screen"
    print >> p, "  -v, --verbose         output verbose debug output"
    print >> p, "  -c, --continous=t,c   Keep pulling every t seconds, c many times c=0 for infinite"
    print >> p, "                        default is to pull once."
    print >> p, "  -f, --format=format   The output format to use:"
    print >> p, "                        default:   The default style output"
    print >> p, "                        csv:       csv style output"
    print >> p, "  -t, --type=TYPE       TYPE=(temphum|anemometer|tachometer|thermocouple|pressure|pressurewide|"
    print >> p, "                              multipointreset|multipointc[1-4]|multipointaddrc[1-4]|ping|"
    print >> p, "                              unitversion|hubversion) *Required"
    print >> p, "  --get-cal             Get calibration value for type"
    print >> p, "  --set-cal=CAL_VALUE   Set calibration value for type"
    print >> p, "  -p, --port=PORT       PORT=#"
    print >> p, "  -a, --address=ADDRESS ADDRESS=#,#,#,..."
    print >> p, "  -u                    use udp instead of serial"
    print >> p, "  -d, --device=PATH     serial device to use for version 3, default /dev/ttyAMA0"
    print >> p, "  -o                    Use direct command code instead of general (aka version2)"
    print >> p, "  -j                    Just send commands then exit immediatly"
    print >> p, "  -s, --server=IP:PORT  Start midsim server listening on IP:PORT"
    print >> p, "  -r, --remote=IP:PORT  Query remote midsim server on IP:PORT"
    print
    print >> p, "  address,port required except for --type=ping"
    print >> p, "  Max number of addresses is 32."

# reopen stdout file descriptor with write mode
# and 0 as the buffer size (unbuffered)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# 'type': [cmd_code, cmd_size, general_req_bool, cal_size]
CC = {'temphum': [1, 4, False, 0], 'anemometer': [2, 2, False, 0], 'tachometer': [3, 2, False, 0],
      'thermocouple': [6, 4, False, 0], 'pressure': [7, 2, False, 0], 'pressurewide': [8, 4, True, 4],
      'multipointreset': [9, 1, True, 0], 'multipointc1': [10, 2, True, 0], 'multipointc2': [11, 2, True, 0],
      'multipointc3': [12, 2, True, 0], 'multipointc4': [13, 2, True, 0], 'multipointaddrc1': [14, 8, True, 0],
      'multipointaddrc2': [15, 8, True, 0], 'multipointaddrc3': [16, 8, True, 0], 'multipointaddrc4': [17, 8, True, 0],
      'unitversion': [63, 2, True, 0], 'hubversion': [150, 2, False, 0], 'ping': [130, 2, False, 0]}

# TODO: Add these as cmd line arguments
udp_selfip = ("10.0.0.28", 1083)
udp_destip = ("10.0.0.29", 1082)
device = "/dev/ttyAMA0"
doUDP = False
verbose = False
justsend = False
format = "default"


def midsim(argv, outstream=sys.stdout, errstream=sys.stderr):
    global justsend, device, verbose, format, doUDP, device, udp_selfip, udp_destip
    try:
        opts, args = getopt.getopt(argv[1:], "hvc:f:p:t:a:ud:ojs:r:",
                                   ["help", "verbose", "continous=", "format=", "port=", "type=", "addresses=",
                                    "device=", "get-cal", "set-cal=", "server=", "remote="])
    except getopt.GetoptError, err:
        print >> outstream, str(err)
        usage(errstream)
        sys.exit(2)
    addrs = None
    port = None
    cmd_code = None
    cmd_codep = None
    cmd_size = None
    general = True
    cal_opts = {"get_cal": False, "set_cal": False, "cal_val": 0, "cal_size": 0}
    loop = [0, 1]
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(outstream)
            sys.exit()
        elif o in ('-r', '--remote'):
            # Copy argv and remove -r or --remote
            newargv = list(argv)
            for i in range(len(newargv)):
                na = newargv[i]
                if na.find('-r') == 0:
                    if len(na) == 2:
                        del newargv[i+1]
                        del newargv[i]
                    else:
                        del newargv[i]
                    break
                elif na.find('--remote') == 0:
                    del newargv[i+1]
                    del newargv[i]
                    break
            server_query(a.strip(), newargv, outstream, errstream)
            return
        elif o in ("-j",):
            justsend = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ('-c', '--continous'):
            loop = [int(a) for a in a.split(",")]
        elif o in ("-f", "--format"):
            if a not in ("default", "csv"):
                print >> errstream, "ERROR: format must be 'csv' or 'default'"
                usage(errstream)
                sys.exit(2)
            else:
                format = a
        elif o in ("-d", "--device"):
            device = a
        elif o in ("-u",):
            doUDP = True
        elif o in ("-o",):
            general = False
        elif o in ('--get-cal',):
            cal_opts["get_cal"] = True
        elif o in ('--set-cal',):
            cal_opts["set_cal"] = True
            cal_opts["cal_val"] = int(a)
        elif o in ("-a", "--addresses"):
            addrs = [int(a) for a in a.split(",")]
        elif o in ("-t", "--type"):
            if a in CC:
                if not general and CC[a][2]:
                    print >> errstream, "ERROR: Direct command code not availible for --type=" + a
                    sys.exit()
                if general:
                    cmd_code = 25
                    cmd_codep = CC[a][0]
                else:
                    cmd_code = CC[a][0]
                cmd_size = CC[a][1]
                cal_opts['cal_size'] = CC[a][3]
                if a == "ping" or a == "hubversion":
                    cmd_code = CC[a][0]
                    addrs = [0]
            else:
                print >> errstream, "Error: invalid type"
                usage(errstream)
                sys.exit(2)
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ("-s", "--server"):
            (server_host, server_port) = a.split(':')
            start_server(server_host, server_port)
            return
        else:
            print >> errstream, "Error: invalid option"
            usage(errstream)
            sys.exit()
    if cmd_code == None:
        print >> errstream, "Error: Missing type"
        usage(errstream)
        sys.exit(2)
    if cmd_code != CC['ping'][0] and cmd_code != CC['hubversion'][0] and port == None:
        print >> errstream, "Error: Missing port."
        usage(errstream)
        sys.exit(2)
    if cmd_code != CC['ping'][0] and cmd_code != CC['hubversion'][0] and addrs == None:
        print >> errstream, "Error: Missing addresses."
        usage(errstream)
        sys.exit(2)
    if (addrs != None and len(addrs) > 32):
        print >> errstream, "Error: must have <= 32 addresses."
        usage(errstream)
        sys.exit(2)
    if cal_opts["set_cal"] and len(addrs) > 1:
        print >> errstream, "Error: Can only set calibration to one unit at a time."
        sys.exit(2)
    if cal_opts["get_cal"] and loop[1] != 1:
        print >> errstream, "Error: Don't loop with calibration commands."
        sys.exit(2)
    if cal_opts["get_cal"] and cal_opts["set_cal"]:
        print >> errstream, "Error: Don't both set and get cal at same time."
        sys.exit(2)
    if cal_opts["get_cal"]:
        if cmd_code == 25:
            cmd_code = 64
        else:
            print >> errstream, "Error: Calibration options need general option."
            sys.exit(2)
    if cal_opts["set_cal"]:
        if cmd_code == 25:
            cmd_code = 65
        else:
            print >> errstream, "Error: Calibration options need general option."
            sys.exit(2)

    if loop[1] <= 0:
        while True:
            run(cmd_code, cmd_codep, cmd_size, port, addrs, cal_opts, outstream, errstream)
            time.sleep(loop[0])
    else:
        for i in xrange(loop[1]):
            run(cmd_code, cmd_codep, cmd_size, port, addrs, cal_opts, outstream, errstream)
            time.sleep(loop[0])


def ds18b20_conversion(v):
    neg = 1.0
    if (v & 0xF800):
        neg = -1.0
        v = ~v + 1
    digits = (v & 0x07F0) >> 4
    decimals = v & 0x000F
    return neg * (digits + decimals / 16.0)


def do_output_start(a, stream):
    if format == 'csv':
        stream.write('"%s"' % (datetime.datetime.strftime(a, "%Y-%m-%d %H:%M:%S.%f")))


def do_output(data, stream):
    if format == 'csv':
        for key in data:
            if key != 'index' and key != 'addr':
                if isinstance(data[key], str):
                    stream.write(',"%s"' % (data[key]))
                else:
                    # Assume a number then
                    stream.write(',%s' % (str(data[key])))
    else:
        stream.write('index: %d' % (data['index']))
        for key in data:
            if (key != 'index'):
                stream.write(', %s: %s' % (key, str(data[key])))
        stream.write('\n')


def do_output_end(stream):
    if format == 'csv':
        stream.write("\n");


def structFormat(calSize):
    t = 'h'
    if calSize == 2:
        t = 'h'
    elif calSize == 4:
        t = 'i'
    elif calSize == 8:
        t = 'q'
    return t


def run(cmd_code, cmd_codep, cmd_size, port, addrs, cal_opts, outstream, errstream):
    ping = random.randrange(1, 60000)
    buffer = "DERV"
    buffer += struct.pack("B", cmd_code)
    if (cmd_code == 1 or cmd_code == 2 or cmd_code == 3 or cmd_code == 6 or cmd_code == 7):  # temphum, wind, tach, thermo
        buffer += struct.pack("BB", port, len(addrs))  # port, N
        for i in addrs:  # Addresses
            buffer += struct.pack("<H", i)
    elif (cmd_code == 25):  # General
        buffer += struct.pack("BBBB", cmd_codep, cmd_size, port, len(addrs))
        for i in addrs:  # Addresses
            buffer += struct.pack("<H", i)
        cmd_code = cmd_codep
    elif (cmd_code == 64):  # Get cal
        buffer += struct.pack("BBBB", cmd_codep, cal_opts['cal_size'], port, len(addrs))
        for i in addrs:  # Addresses
            buffer += struct.pack("<H", i)
    elif (cmd_code == 65):  # Set cal
        buffer += struct.pack("<BBBH" + structFormat(cal_opts['cal_size']), cmd_codep, cal_opts['cal_size'], port,
                              addrs[0], cal_opts['cal_val'])
    elif (cmd_code == CC['ping'][0] or cmd_code == CC['hubversion'][0]):  # Ping or hubversion
        if (verbose):
            print >> outstream, "DEBUG: ping = " + str(ping)
        buffer += struct.pack("<H", ping)

    if (doUDP):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(udp_selfip)
    else:
        s = serial.Serial(device, 9600, timeout=10 * len(addrs))

    if (verbose):
        print >> outstream, "Sending command."
        for i in range(len(buffer)):
            print >> outstream, " " + str(ord(buffer[i])),
        print >> outstream
    if (doUDP):
        s.sendto(buffer, udp_destip)
    else:
        s.write(buffer)
    if justsend:
        sys.exit(0)

    # s.close()
    # sys.exit(0)
    if (verbose):
        print >> outstream, "Awaiting reply"
    if (doUDP):
        rstr = s.recv(512)
    else:
        # length only Hub to ethernet board
        l = struct.unpack("<H", s.read(2))[0]
        if (verbose):
            print >> outstream, "DEBUG: told recieved bytes: " + str(l)
        rstr = s.read(l - 2)

    if (verbose):
        print >> outstream, "DEBUG: bytes in reply: " + str(len(rstr))
        print >> outstream, "DEBUG: ord contents: ",
    if (verbose):
        for i in range(len(rstr)):
            print >> outstream, str(ord(rstr[i])),
            print >> outstream
    rbuf = StringIO(rstr)

    do_output_start(datetime.datetime.now(), outstream)
    codeS = rbuf.read(1)
    while (len(codeS) != 0):
        code = ord(codeS)
        if (verbose):
            print >> outstream, "DEBUG: Reply code " + str(code)
        if code == 1:
            s = ord(rbuf.read(1))
            cc = ord(rbuf.read(1))
            if verbose:
                print >> outstream, "DEBUG: cc=%d" % (cc)
            if (cc != cmd_code):
                print >> errstream, "ERROR: Command codes mismatch %d != %d" % (cc, cmd_code)
                sys.exit(3)
            n = ord(rbuf.read(1))
            if (n != len(addrs)):
                print >> errstream, "ERROR: N != len(addrs)"
                sys.exit(3)
            if (s != cmd_size * len(addrs) + 1):
                print >> errstream, "ERROR: weird datasize s=" + str(s)
                sys.exit(3)
            if (cmd_code == CC['temphum'][0]):
                for i in range(n):
                    (temp, hum) = struct.unpack("<HH", rbuf.read(4))
                    if (temp != 0):
                        temp = (-40.2) + 0.018 * temp
                        h = -2.0468 + 0.0367 * hum + -1.5955e-6 * hum ** 2
                        h = (((temp - 32.0) / 1.8) - 25) * (0.01 + 0.00008 * hum) + h
                        data = {'index': (i + 1), 'addr': str(port) + ':' + str(addrs[i]), 'temp': temp, 'humidity': h,
                                'BMEHum': hum / 100.0}
                        do_output(data, outstream)
                    # print "A: "+str(i+1)+", T:"+str(temp)+", H:"+str(h)
                    else:
                        do_output({'index': (i + 1), 'addr': str(port) + ':' + str(addrs[i]), 'temp': 'ERR',
                                   'humidity': 'ERR'}, outstream)
                    # print "A: "+str(i+1)+", T:ERR, H:ERR"
            elif (cmd_code == CC['anemometer'][0]):
                for i in range(n):
                    v = struct.unpack("<H", rbuf.read(2))[0]
                    if (v != 0):
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'velocity': v}, outstream)
                    # print "A: "+str(i+1)+", V:"+str(v)
                    else:
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'velocity': 'ERR'},
                                  outstream)
                    # print "A: "+str(i+1)+", V:ERR"
            elif (cmd_code == CC['tachometer'][0]):
                for i in range(n):
                    v = struct.unpack("<H", rbuf.read(2))[0]
                    if (v != 0):
                        # print "A: "+str(i+1)+", R:"+str(v)
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'velocity': v}, outstream)
                    else:
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'velocity': 'ERR'},
                                  outstream)
                    # print "A: "+str(i+1)+", R:ERR"
            elif (cmd_code == CC['thermocouple'][0]):
                for i in range(n):
                    (temp1, temp2) = struct.unpack("<HH", rbuf.read(4))
                    if (temp1 != 0 or temp2 != 0):
                        temp1 = (1023.75 * temp1 / (2 ** 12)) * 9. / 5. + 32.0
                        temp2 = (1023.75 * temp2 / (2 ** 12)) * 9. / 5. + 32.0
                        # print "A: "+str(i+1)+", T1:"+str(temp1)+", T2:"+str(temp2)
                        do_output(
                            {'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'temp1': temp1, 'temp2': temp2},
                            outstream)
                    else:
                        # print "A: "+str(i+1)+", T1:ERR, T2:ERR"
                        do_output(
                            {'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'temp1': 'ERR', 'temp2': 'ERR'},
                            outstream)
            elif (cmd_code == CC['pressure'][0]):
                for i in range(n):
                    p = struct.unpack("<H", rbuf.read(2))[0]
                    if (p != 0):
                        p = 0.0022888 * p + 50.0
                        # print "R: "+str(i+1)+", P:"+str(p)
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'pressure': p}, outstream)
                    else:
                        # print "R: "+str(i+1)+", P:ERR"
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'pressure': 'ERR'},
                                  outstream)
            elif (cmd_code == CC['pressurewide'][0]):
                for i in range(n):
                    p = struct.unpack("<I", rbuf.read(4))[0]
                    if (p != 0):
                        p = p
                        # print "R: "+str(i+1)+", P:"+str(p)
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'pressure': p}, outstream)
                    else:
                        # print "R: "+str(i+1)+", P:ERR"
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'pressure': 'ERR'},
                                  outstream)
            elif (cmd_code == CC['multipointreset'][0]):
                for i in range(n):
                    p = ord(rbuf.read(1))
                    if (p != 0):
                        # print "R: "+str(i+1)+", P:"+str(p)
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'reset': p}, outstream)
                    else:
                        # print "R: "+str(i+1)+", P:ERR"
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'reset': 'ERR'}, outstream)
            elif (cmd_code >= CC['multipointc1'][0] and cmd_code <= CC['multipointc4'][0]):
                for i in range(n):
                    p = struct.unpack("<H", rbuf.read(2))[0]
                    if (p != 0):
                        p = 1.8 * ds18b20_conversion(p) + 32
                        # print "R: "+str(i+1)+", T:"+str(p)
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'temp': p}, outstream)
                    else:
                        # print "R: "+str(i+1)+", T:ERR"
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'temp': 'ERR'}, outstream)
            elif (cmd_code >= CC['multipointaddrc1'][0] and cmd_code <= CC['multipointaddrc4'][0]):
                for i in range(n):
                    p = struct.unpack("<Q", rbuf.read(8))[0]
                    if (p != 0):
                        # print "R: "+str(i+1)+", T:"+str(p)
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'saddr': hex(p)}, outstream)
                    else:
                        # print "R: "+str(i+1)+", T:ERR"
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'temp': 'ERR'}, outstream)
            elif (cmd_code == CC['unitversion'][0]):
                for i in range(n):
                    v = struct.unpack("<H", rbuf.read(2))[0]
                    if (v != 0):
                        # print "A: "+str(i+1)+", R:"+str(v)
                        do_output(
                            {'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'unitversion': 3.0 + v / 100.0},
                            outstream)
                    else:
                        do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'unitversion': 'ERR'},
                                  outstream)
            elif (cmd_code == 64 or cmd_code == 65):
                for i in range(n):
                    v = struct.unpack("<" + structFormat(cal_opts['cal_size']), rbuf.read(cal_opts['cal_size']))[0]
                    # print "A: "+str(i+1)+", R:"+str(v)
                    do_output({'index': i + 1, 'addr': str(port) + ':' + str(addrs[i]), 'calibration': v}, outstream)
        elif code == 3:
            p = struct.unpack("<H", rbuf.read(2))[0]
            # print "PONG: "+str(p)
            do_output({'index': 0, 'pong': p}, outstream)
        elif code == 4:
            l = ord(rbuf.read(1))
            for i in range(l):
                (c, a) = struct.unpack("BB", rbuf.read(2))
                if format != 'csv':
                    print >> errstream, "Error: " + str(i + 1) + ", Code: " + str(c) + ", AddrIdx:" + str(a)
        elif code == 5:
            p = struct.unpack("<H", rbuf.read(2))[0]
            # print "HUB VERSION: "+str(p)
            do_output({'index': 0, 'hubversion': 3.0 + p / 100.0}, outstream)
        else:
            print >> outstream, "BIG error: unknown reply code " + str(code) + "."
            print >> errstream, "BIG error: unknown reply code " + str(code) + "."
        codeS = rbuf.read(1)
    do_output_end(outstream)


if __name__ == "__main__":
    midsim(sys.argv)
