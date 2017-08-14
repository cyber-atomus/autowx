#!/usr/bin/env python
# -*- coding: utf-8 -*-

import predict
import time
from time import strftime
import sys, os
import cfg

configFile = 'autowx.ini'

if len(sys.argv) > 2:
    print("Usage: {} [autowx.ini]".format(sys.argv[0]))
    exit(-1)
elif len(sys.argv) == 2:
    configFile = sys.argv[1]

config = cfg.get(configFile)

# Config
elNOAA = config.getint('QTH', 'minElev')
elMETEOR = config.getint('QTH', 'minElevMeteor')
tleFileName = os.path.join(config.get('DIRS', 'tle'), config.get('DIRS', 'tleFile'))
qth = (config.getfloat('QTH', 'lat'), config.getfloat('QTH', 'lon'), config.getint('QTH', 'alt'))

# The rest
NOAA15 = []
NOAA18 = []
NOAA19 = []
METEORM2 = []
birds = [NOAA15, NOAA18, NOAA19, METEORM2]
g = []

tlefile = open(tleFileName, 'r')
tledata = tlefile.readlines()
tlefile.close()

for i, line in enumerate(tledata):
    if "NOAA 15" in line:
        for l in tledata[i:i + 3]: NOAA15.append(l.strip('\r\n').rstrip()),
for i, line in enumerate(tledata):
    if "NOAA 18" in line:
        for m in tledata[i:i + 3]: NOAA18.append(m.strip('\r\n').rstrip()),
for i, line in enumerate(tledata):
    if "NOAA 19" in line:
        for n in tledata[i:i + 3]: NOAA19.append(n.strip('\r\n').rstrip()),
for i, line in enumerate(tledata):
    if "METEOR-M 2" in line:
        for n in tledata[i:i + 3]: METEORM2.append(n.strip('\r\n').rstrip()),

time_start = time.time()
time_end = time.time() + 86400

printEl = 0
minEl = 20

for h in birds:
    print h[0]
    if h[0] in ('NOAA 15', 'NOAA 18', 'NOAA 19'):
        minEl = elNOAA
    elif h[0] == 'METEOR-M 2':
        minEl = elMETEOR
    p = predict.transits(h, qth, time_start)
    for i in range(1, 20):
        transit = p.next()
        minuty = time.strftime("%M:%S", time.gmtime(transit.duration()))
        if int(transit.peak()['elevation']) >= minEl:
            print "** " + strftime('%d-%m-%Y %H:%M:%S', time.localtime(transit.start)) + " (" + str(
                int(transit.start)) + ") to " + strftime('%d-%m-%Y %H:%M:%S', time.localtime(
                transit.start + int(transit.duration()))) + " (" + str(
                int(transit.start + int(transit.duration()))) + ")" + ", dur: " + str(
                int(transit.duration())) + " sec (" + str(minuty) + "), max el. " + str(
                int(transit.peak()['elevation'])) + " deg."
        else:
            if str(printEl) in "1":
                print "!! " + strftime('%d-%m-%Y %H:%M:%S', time.localtime(transit.start)) + " (" + str(
                    int(transit.start)) + ") to " + strftime('%d-%m-%Y %H:%M:%S', time.localtime(
                    transit.start + int(transit.duration()))) + " (" + str(
                    int(transit.start + int(transit.duration()))) + ")" + ", dur:" + str(
                    int(transit.duration())) + "s. ,max " + str(int(transit.peak()['elevation'])) + " el."
