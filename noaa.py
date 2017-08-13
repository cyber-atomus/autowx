#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
from time import gmtime, strftime
import pypredict
import subprocess
import os
import os, shutil
import re
import sys
import cfg

if len(sys.argv) > 2:
	print("Usage: {} [autowx.ini]".format(sys.argv[0]))
	exit(-1)
elif len(sys.argv) == 2:
	configFile = sys.argv[1]
else:
	configFile = 'autowx.ini'

config = cfg.get(configFile)

	###############################
	###                          ##
	###     Here be dragons.     ##
	###                          ##
	###############################


# Read qth file for station data

stationLonNeg=float(config.get('QTH', 'lon'))*-1
tleFileDir=os.path.join(config.get('DIRS', 'tle'), config.get('DIRS', 'tleFile'))

class bcolors:
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[97m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[37m'
    UNDERLINE = '\033[4m'

logLineStart=bcolors.BOLD+bcolors.HEADER+"***>\t"+bcolors.ENDC+bcolors.OKGREEN
logLineEnd=bcolors.ENDC

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

pid = str(os.getpid())
if os.path.isfile(config.get('LOG', 'pid')):
    os.unlink(config.get('LOG', 'pid'))
file(config.get('LOG', 'pid'), 'w').write(pid)

if config.getboolean('LOG', 'enable'):
    sys.stdout = Logger(config.get('LOG', 'filename'))

if config.getboolean('PROCESSING', 'wxQuietOutput'):
    wxQuietOpt='-q'
else:
    wxQuietOpt='-C wxQuiet:no'

if config.getboolean('PROCESSING', 'wxDecodeAll'):
    wxDecodeOpt='-A'
else:
    wxDecodeOpt='-C wxDecodeAll:no'

if config.getboolean('PROCESSING', 'wxAddTextOverlay'):
    wxAddText='-k ' + config.get('PROCESSING', 'wxOverlayText') + ' %g %T/%E%p%^%z/e:%e %C'
else:
    wxAddText='-C wxOther:noOverlay'

##
## Execution loop declaration
##

def runForDuration(cmdline, duration):
    try:
        child = subprocess.Popen(cmdline)
        time.sleep(duration)
        child.terminate()
    except OSError as e:
        print "OS Error during command: "+" ".join(cmdline)
        print "OS Error: "+e.strerror

##
## FM Recorder definition
##

def recordFM(freq, fname, duration, xfname):
    print bcolors.GRAY
    xfNoSpace=xfname.replace(" ","")
    cmdline = ['/usr/bin/rtl_fm',\
		'-f',str(freq),\
		'-s',config.getint('SDR', 'sample'),\
		'-g',config.getint('SDR', 'gain'),\
		'-F','9',\
		'-l','0',\
		'-t','900',\
		'-A','fast',\
		'-E','offset',\
#		'-E','pad',\
		'-p',config.getint('SDR', 'shift'), \
		config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.raw']
    runForDuration(cmdline, duration)

def recordQPSK(duration):
    print bcolors.GRAY
    xfNoSpace=xfname.replace(" ","")
    cmdline = [config.get('DIRS', 'system')+'/meteor_qpsk.py', configFile]
    runForDuration(cmdline, duration)

##
## Status builder. Crazy shit. These are only examples, do what you want :)
##

def writeStatus(freq, aosTime, losTime, losTimeUnix, recordTime, xfName, maxElev, status):
    aosTimeStr=strftime('%H:%M:%S', time.localtime(aosTime))
    passImgFile=strftime('%Y%m%d-%H%M', time.localtime(aosTime))+'-pass-img.png'
    statFile=open(config.get('DIRS', 'status'), 'w+')
    if status in ('RECORDING'):
	statFile.write("ODBIOR;tak;"+str(xfName)+' AOS@'+str(aosTimeStr)+' LOS@'+str(losTime)+' REC@'+str(recordTime)+'s. max el.@'+str(maxElev)+'°'+';'+str(xfName)+'-'+strftime('%Y%m%d-%H%M', time.localtime(aosTime)))
    elif status in ('DECODING'):
	statFile.write('ODBIOR;nie;Dekodowanie '+str(xfName)+';'+str(xfName)+'-'+strftime('%Y%m%d-%H%M', time.localtime(aosTime)))
    elif status in ('WAITING'):
	statFile.write('ODBIOR;nie;'+str(xfName)+' (AOS@'+str(aosTimeStr)+') @'+str(maxElev)+'° elev. max'+';'+str(xfName)+'-'+strftime('%Y%m%d-%H%M', time.localtime(losTimeUnix)))
    elif status in ('TOOLOW'):
	statFile.write('ODBIOR;nie;'+str(xfName)+' (AOS@'+str(aosTimeStr)+') zbyt nisko ('+str(maxElev)+'°), czekam '+str(recordTime)+'s.')
    statFile.close

##
## Transcoding module
##

def transcode(fname):
    xfNoSpace=xfname.replace(" ","")
    print logLineStart+'Transcoding...'+bcolors.YELLOW
    cmdlinesox = ['sox','-t','raw','-r',config.getint('SDR', 'sample'),'-es','-b','16','-c','1','-V1',config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.raw',config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav','rate',config.getint('SDR', 'wavrate')]
    subprocess.call(cmdlinesox)
    cmdlinetouch = ['touch','-r'+config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.raw',config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav']
    subprocess.call(cmdlinetouch)
    if config.getboolean('PROCESSING', 'removeRAW'):
	print logLineStart+bcolors.ENDC+bcolors.RED+'Removing RAW data'+logLineEnd
	os.remove(config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.raw')


def createoverlay(fname,aosTime,satName,recLen):
    print logLineStart+'Creating Map Overlay...'+logLineEnd
    aosTimeO=int(aosTime)+int('1')
    recLenC=int(recLen)
    #recLenC='2'
    mapfname = os.path.join(config.get('DIRS', 'map'), fname)
    cmdline = ['wxmap',
    '-T',satName,\
    '-G',str(config.get('DIRS', 'tle')),\
    '-H',str(config.get('DIRS', 'tleFile')),\
    '-M','0',\
    '-o', \
    '-A','0', \
    '-O',str(recLenC), \
    '-L',config.get('QTH', 'lat')+'/'+config.get('QTH', 'lat')+'/'+config.get('QTH', 'alt'),\
    str(aosTimeO), mapfname+'-map.png']
    overlay_log = open(mapfname+'-map.png.txt',"w+")
    subprocess.call(cmdline, stderr=overlay_log, stdout=overlay_log)
    overlay_log.close()

def decodeQPSK():
    subprocess.Popen(config.get('DIRS', 'system')+'/decode_meteor.sh')

def decode(fname,aosTime,satName,maxElev,recLen):
    xfNoSpace=xfname.replace(" ","")
    satTimestamp = int(fname)
    fileNameC = datetime.datetime.fromtimestamp(satTimestamp).strftime('%Y%m%d-%H%M')

    if config.getboolean('PROCESSING', 'wxAddOverlay'):
	print logLineStart+bcolors.OKBLUE+'Creating overlay map'+logLineEnd
	createoverlay(fname,aosTime,satName,recLen)
	print logLineStart+'Creating basic image with overlay map'+logLineEnd
	m = open(config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',"w+")
	m.write('\nSAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
	for psikus in open(config.get('DIRS', 'map')+'/'+str(fname)+'-map.png.txt',"r").readlines():
	    res=psikus.replace("\n", " \n")
	    m.write(res)
	cmdline = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxAddText,'-A','-o','-R1','-t','NOAA','-Q '+config.getint('PROCESSING', 'wxJPEGQuality'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg']
	subprocess.call(cmdline, stderr=m, stdout=m)
	m.close()
	for line in open(config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',"r").readlines():
	    res=line.replace("\n", "")
	    res2=re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
	    print logLineStart+bcolors.OKBLUE+res2+logLineEnd
	    if "Channel A" in res: 
		chan1=res.rstrip().replace('(',':').split(':')
		channelA=chan1[1].strip().rstrip()[:1]
	    if "Channel B" in res: 
		chan1=res.rstrip().replace('(',':').split(':')
		channelB=chan1[1].strip().rstrip()[:1]

#Copy logs
	if config.getboolean('SCP', 'log'):
	    print logLineStart+"Sending flight and decode logs..."+bcolors.YELLOW
	    cmdline_scp_log = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal-map.jpg.txt' ]
	    subprocess.call(cmdline_scp_log)
	if config.getboolean('SCP', 'img'):
	    print logLineStart+"Sending base image with map: "+bcolors.YELLOW
	    cmdline_scp_img = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal-map.jpg' ]
	    subprocess.call(cmdline_scp_img)
	    print logLineStart+"Sending OK, go on..."+logLineEnd
## NOWE
	if config.getboolean('PROCESSING', 'wxEnhCreate'):
	    print "Channel A:"+channelA+", Channel B:"+channelB
	    for enhancements in config.getlist('PROCESSING', 'wxEnhList'):
		print logLineStart+'Creating '+enhancements+' enhancement image'+logLineEnd
		enhancements_log = open(config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg.txt',"w+")
		enhancements_log.write('\nEnhancement: '+enhancements+', SAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
		if enhancements in ('HVCT', 'HVC'):
		    if channelA in "1" and channelB in "2":
			print "1 i 2"
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K0','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    elif channelA in "1" and channelB in "1":
			print "1 i 1 "
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K0','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    elif channelA in "1" and channelB in "4":
			print "1 i 4 "
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K0','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    elif channelA in "1" and channelB in "3":
			print "1 i 3"
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K3','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    elif channelA in "2" and channelB in "4":
			print "2 i 4"
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K1','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    elif channelA in "3" and channelB in "4":
			print "3 i 4"
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K4','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    else:
			print "Kanaly nieznane"
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-K1','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		if enhancements in ('MSA'):
		    if channelA in ("1", "2") and channelB in "4":
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		    else:
			cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-eNO','-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		else:
		    cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-A','-o','-c','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,'-m',config.get('DIRS', 'map')+'/'+fname+'-map.png'+','+config.get('PROCESSING', 'wxOverlayOffsetX')+','+config.get('PROCESSING', 'wxOverlayOffsetY'),config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg']
		subprocess.call(cmdline_enhancements, stderr=enhancements_log, stdout=enhancements_log)
		for psikus in open(config.get('DIRS', 'map')+'/'+str(fname)+'-map.png.txt',"r").readlines():
		    res=psikus.replace("\n", " \n")
		    enhancements_log.write(res)
		enhancements_log.close()
		if config.getboolean('SCP', 'log'):
		    print logLineStart+"Sending "+enhancements+" flight and decode logs..."+bcolors.YELLOW
		    cmdline_scp_log = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg.txt',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-'+enhancements+'-map.jpg.txt' ]
		    subprocess.call(cmdline_scp_log)
		    print logLineStart+"Sending logs OK, moving on..."+logLineEnd
		if config.getboolean('SCP', 'img'):
		    print logLineStart+"Sending "+enhancements+" image with overlay map... "+bcolors.YELLOW
		    cmdline_scp_img = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-'+enhancements+'-map.jpg' ]
		    subprocess.call(cmdline_scp_img)
		    print logLineStart+"Send image OK, moving on..."+logLineEnd

# SFPG
	if config.getboolean('SCP', 'sfpgLink'):
	    sciezka_plik=config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-MCIR-precip-map.jpg'
	    sciezka_plik2=config.get('DIRS', 'img')+'/'+satName+'/_image.jpg'
    	    if os.path.isfile(sciezka_plik2):
		os.unlink(sciezka_plik2)
	    os.symlink(sciezka_plik,sciezka_plik2)
    else:
	print logLineStart+'Creating basic image without map'+logLineEnd
	r = open(config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal.jpg.txt',"w+")
	cmdline = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-o','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-t','NOAA',config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav', config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal.jpg']
	r.write('\nSAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
	subprocess.call(cmdline, stderr=r, stdout=r)
	r.close()
	for line in open(config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal.jpg.txt',"r").readlines():
	    res=line.replace("\n", "")
	    res2=re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
	    print logLineStart+bcolors.OKBLUE+res2+logLineEnd
	if config.getboolean('SCP', 'log'):
	    print logLineStart+"Sending flight and decode logs..."+bcolors.YELLOW
	    cmdline_scp_log = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal-map.jpg.txt' ]
	    subprocess.call(cmdline_scp_log)
	if config.getboolean('SCP', 'img'):
	    print logLineStart+"Sending base image with map: "+bcolors.YELLOW
	    cmdline_scp_img = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-normal-map.jpg',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal-map.jpg' ]
	    subprocess.call(cmdline_scp_img)
	    print logLineStart+"Sending OK, go on..."+logLineEnd
	if config.getboolean('PROCESSING', 'wxEnhCreate'):
	    for enhancements in config.getlist('PROCESSING', 'wxEnhList'):
		print logLineStart+'Creating '+enhancements+' image'+logLineEnd
		enhancements_log = open(config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-nomap.jpg.txt',"w+")
		enhancements_log.write('\nEnhancement: '+enhancements+', SAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
		cmdline_enhancements = [ config.get('DIRS', 'wxInstall')+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-o','-K','-R1','-Q '+config.get('PROCESSING', 'wxJPEGQuality'),'-e',enhancements,config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-nomap.jpg']
		subprocess.call(cmdline_enhancements, stderr=enhancements_log, stdout=enhancements_log)
		enhancements_log.close()
		if config.getboolean('SCP', 'log'):
		    print logLineStart+"Sending "+enhancements+" flight and decode logs..."+bcolors.YELLOW
		    cmdline_scp_log = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg.txt',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-'+enhancements+'-map.jpg.txt' ]
		    subprocess.call(cmdline_scp_log)
		if config.getboolean('SCP', 'img'):
		    print logLineStart+"Sending "+enhancements+" image with overlay map... "+bcolors.YELLOW
		    cmdline_scp_img = [ '/usr/bin/scp',config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-'+enhancements+'-map.jpg',config.get('SCP', 'user')+'@'+config.get('SCP', 'host')+':'+config.get('SCP', 'dir')+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-'+enhancements+'-map.jpg' ]
		    subprocess.call(cmdline_scp_img)
		    print logLineStart+"Sending OK, moving on"+logLineEnd

	if config.getboolean('SCP', 'sfpgLink'):
	    sciezka_plik=config.get('DIRS', 'img')+'/'+satName+'/'+fileNameC+'-MCIR-precip-nomap.jpg'
	    sciezka_plik2=config.get('DIRS', 'img')+'/'+satName+'/_image.jpg'
    	    if os.path.isfile(sciezka_plik2):
		os.unlink(sciezka_plik2)
	    os.symlink(sciezka_plik,sciezka_plik2)

##
## Record and transcode wave file
##

def recordWAV(freq,fname,duration,xfname):
    recordFM(freq,fname,duration,xfname)
    transcode(fname)
    if config.getboolean('PROCESSING', 'createSpectro'):
        spectrum(fname)

def spectrum(fname):
    xfNoSpace=xfname.replace(" ","")
    print logLineStart+'Creating flight spectrum'+logLineEnd
    cmdline = ['sox',config.get('DIRS', 'rec')+'/'+xfNoSpace+'-'+fname+'.wav', '-n', 'spectrogram','-o',config.get('DIRS', 'spec')+'/'+xfNoSpace+'-'+fname+'.png']
    subprocess.call(cmdline)

def findNextPass():
    predictions = [pypredict.aoslos(s,config.get('QTH', 'minElev'),config.get('QTH', 'minElevMeteor'),config.get('QTH', 'lat'),config.get('QTH', 'lon'),config.get('QTH', 'alt'),tleFileDir) for s in config.getlist('BIRDS', 'satellites')]
    aoses = [p[0] for p in predictions]
    nextIndex = aoses.index(min(aoses))
    return (config.getlist('BIRDS', 'satellites')[nextIndex], \
			config.getlist('BIRDS', 'freqs')[nextIndex],\
            predictions[nextIndex]) 

##
## Now magic
##

while True:
    (satName, freq, (aosTime, losTime, duration, maxElev)) = findNextPass()
    now = time.time()
    towait = aosTime-now

    aosTimeCnv=strftime('%H:%M:%S', time.localtime(aosTime))
    emergeTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(aosTime))
    losTimeCnv=strftime('%H:%M:%S', time.localtime(losTime))
    dimTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(losTime))
##
## OK, now we have to decide what if recording or sleeping
##
    if towait>0:
        print logLineStart+"waiting "+bcolors.CYAN+str(towait).split(".")[0]+bcolors.OKGREEN+" seconds  ("+bcolors.CYAN+aosTimeCnv+bcolors.OKGREEN+" to "+bcolors.CYAN+losTimeCnv+", "+str(duration)+bcolors.OKGREEN+"s.) for "+bcolors.YELLOW+satName+bcolors.OKGREEN+" @ "+bcolors.CYAN+str(maxElev)+bcolors.OKGREEN+"° el. "+logLineEnd
        writeStatus(freq,aosTime,losTimeCnv,aosTime,towait,satName,maxElev,'WAITING')
    	time.sleep(towait)

    if aosTime<now:
        recordTime=losTime-now
        if recordTime<1:
	    recordTime=1
    elif aosTime>=now:
	recordTime=duration
    	if recordTime<1:
	    recordTime=1
##
    fname=str(aosTime)
    xfname=satName
    print logLineStart+"Beginning pass of "+bcolors.YELLOW+satName+bcolors.OKGREEN+" at "+bcolors.CYAN+str(maxElev)+"°"+bcolors.OKGREEN+" elev.\n"+logLineStart+"Predicted start "+bcolors.CYAN+aosTimeCnv+bcolors.OKGREEN+" and end "+bcolors.CYAN+losTimeCnv+bcolors.OKGREEN+".\n"+logLineStart+"Will record for "+bcolors.CYAN+str(recordTime).split(".")[0]+bcolors.OKGREEN+" seconds."+logLineEnd
    writeStatus(freq,aosTime,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,maxElev,'RECORDING')
#
    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
	recordWAV(freq,fname,recordTime,xfname)
    elif xfname in ('METEOR-M 2'):
	recordQPSK(recordTime)
    print logLineStart+"Decoding data"+logLineEnd
    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
        writeStatus(freq,aosTime,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,maxElev,'DECODING')
        decode(fname,aosTime,satName,maxElev,recordTime) # make picture
    elif xfname in ('METEOR-M 2'):
	if config.getboolean('PROCESSING', 'decodeMeteor'):
	    print "This may take a loooong time and is resource hungry!!!"
	    writeStatus(freq,aosTime,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,maxElev,'DECODING')
	    decodeQPSK()
    print logLineStart+"Finished pass of "+bcolors.YELLOW+satName+bcolors.OKGREEN+" at "+bcolors.CYAN+losTimeCnv+bcolors.OKGREEN+". Sleeping for"+bcolors.CYAN+" 10"+bcolors.OKGREEN+" seconds"+logLineEnd
    time.sleep(10.0)

