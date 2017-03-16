#!/usr/bin/env python
# -*- coding: utf-8 -*-

import predict
import time
import datetime
from time import gmtime, strftime

elNOAA=20
elMETEOR=35
tleFileName='/tmp/weather.txt'

NOAA15=[]
NOAA18=[]
NOAA19=[]
METEORM2=[]
ktore=[ NOAA15, NOAA18, NOAA19, METEORM2 ]
g = []

tlefile=open(tleFileName, 'r')
tledata=tlefile.readlines()
tlefile.close()


for i, line in enumerate(tledata):
    if "NOAA 15" in line: 
        for l in tledata[i:i+3]: NOAA15.append(l.strip('\r\n').rstrip()),
for i, line in enumerate(tledata):
    if "NOAA 18" in line: 
        for m in tledata[i:i+3]: NOAA18.append(m.strip('\r\n').rstrip()),
for i, line in enumerate(tledata):
    if "NOAA 19" in line: 
        for n in tledata[i:i+3]: NOAA19.append(n.strip('\r\n').rstrip()),
for i, line in enumerate(tledata):
    if "METEOR-M 2" in line: 
        for n in tledata[i:i+3]: METEORM2.append(n.strip('\r\n').rstrip()),

qth = (53.34045, -15.05793, 5)

czasStart=time.time()
czasKoniec=time.time()+86400


printEl=0

for h in ktore:
    print h[0]
    if h[0] in ('NOAA 15', 'NOAA 18', 'NOAA 19'):
	minEl=elNOAA
    elif h[0] in ('METEOR-M 2'):
	minEl=elMETEOR
    p = predict.transits(h, qth, czasStart)
    for i in range(1,20):
	transit = p.next()
	minuty=time.strftime("%M:%S", time.gmtime(transit.duration()))
	if int(transit.peak()['elevation'])>=minEl:
	    print "** "+strftime('%d-%m-%Y %H:%M:%S', time.localtime(transit.start))+" ("+str(int(transit.start))+") to "+strftime('%d-%m-%Y %H:%M:%S', time.localtime(transit.start+int(transit.duration())))+" ("+str(int(transit.start+int(transit.duration())))+")"+", dur: "+str(int(transit.duration()))+" sec ("+str(minuty)+"), max el. "+str(int(transit.peak()['elevation']))+" deg."
	else:
	    if str(printEl) in "1":
		print "!! "+strftime('%d-%m-%Y %H:%M:%S', time.localtime(transit.start))+" ("+str(int(transit.start))+") to "+strftime('%d-%m-%Y %H:%M:%S', time.localtime(transit.start+int(transit.duration())))+" ("+str(int(transit.start+int(transit.duration())))+")"+", dur:"+str(int(transit.duration()))+"s. ,max "+str(int(transit.peak()['elevation']))+" el."
