#!/usr/bin/env python
# -*- coding: utf-8 -*-

import predict
import time



def aoslos(satname,minElev,minElevMeteor,stationLat,stationLon,stationAlt,tleFile):
    tleNOAA15=[]
    tleNOAA18=[]
    tleNOAA19=[]
    tleMETEOR=[]
    
    tlefile=open(str(tleFile))
    tledata=tlefile.readlines()
    tlefile.close()

    for i, line in enumerate(tledata):
	if "NOAA 15" in line: 
    	    for l in tledata[i:i+3]: tleNOAA15.append(l.strip('\r\n').rstrip()),
    for i, line in enumerate(tledata):
	if "NOAA 18" in line: 
    	    for m in tledata[i:i+3]: tleNOAA18.append(m.strip('\r\n').rstrip()),
    for i, line in enumerate(tledata):
	if "NOAA 19" in line: 
    	    for n in tledata[i:i+3]: tleNOAA19.append(n.strip('\r\n').rstrip()),
    for i, line in enumerate(tledata):
	if "METEOR-M 2" in line: 
    	    for n in tledata[i:i+3]: tleMETEOR.append(n.strip('\r\n').rstrip()),

    qth=(float(stationLat),float(stationLon),float(stationAlt))
    minElev=int(minElev)
    minElevMeteor=int(minElevMeteor)
# Recording delay
    opoznienie='1'
# delay meteor to ~12° - 15°
    meteor_delay='180'
# Recording short
    skrocenie='1'
# Shorten meteor recording by ~12° - 15°
    meteor_short='180'
# Predicting
    if satname in "NOAA 15":
	p = predict.transits(tleNOAA15, qth)
	for i in range(1,20):
	    transit = p.next()
	    przelot_start=int(transit.start)+int(opoznienie)
	    przelot_czas=int(transit.duration())-(int(skrocenie)+int(opoznienie))
	    przelot_koniec = int(przelot_start)+int(przelot_czas)
	    if int(transit.peak()['elevation'])>=minElev:
		return(int(przelot_start), int(przelot_koniec), int(przelot_czas), int(transit.peak()['elevation']))
    elif satname in "NOAA 18":
	p = predict.transits(tleNOAA18, qth)
	for i in range(1,20):
	    transit = p.next()
	    przelot=int(transit.duration())
	    przelot_start=int(transit.start)+int(opoznienie)
	    przelot_czas=int(transit.duration())-(int(skrocenie)+int(opoznienie))
	    przelot_koniec = int(przelot_start)+int(przelot_czas)
	    if int(transit.peak()['elevation'])>=minElev:
	    	return(int(przelot_start), int(przelot_koniec), int(przelot_czas), int(transit.peak()['elevation']))
    elif satname in "NOAA 19":
	p = predict.transits(tleNOAA19, qth)
	for i in range(1,20):
	    transit = p.next()
	    przelot_start=int(transit.start)+int(opoznienie)
	    przelot_czas=int(transit.duration())-(int(skrocenie)+int(opoznienie))
	    przelot_koniec = int(przelot_start)+int(przelot_czas)
	    if int(transit.peak()['elevation'])>=minElev:
		return(int(przelot_start), int(przelot_koniec), int(przelot_czas), int(transit.peak()['elevation']))
    elif satname in "METEOR-M 2":
	p = predict.transits(tleMETEOR, qth)
	for i in range(1,20):
	    transit = p.next()
	    przelot_start=int(transit.start)+int(meteor_delay)
	    przelot_czas=int(transit.duration())-(int(meteor_short)+int(meteor_delay))
	    przelot_koniec = int(przelot_start)+int(przelot_czas)
	    if int(transit.peak()['elevation'])>=minElevMeteor:
		return(int(przelot_start), int(przelot_koniec), int(przelot_czas), int(transit.peak()['elevation']))
    else:
	print "NO TLE DEFINED FOR "+satname+" BAILING OUT"
