#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
from time import strftime
import pypredict
import subprocess
import os
import re
import sys
import cfg

configFile = 'autowx.ini'

if len(sys.argv) > 2:
    print("Usage: {} [autowx.ini]".format(sys.argv[0]))
    exit(-1)
elif len(sys.argv) == 2:
    configFile = sys.argv[1]

config = cfg.get(configFile)

#############################
#                          ##
#     Here be dragons.     ##
#                          ##
#############################

stationLonNeg = float(config.get('QTH', 'lon')) * -1
tleFileDir = os.path.join(config.get('DIRS', 'tle'), config.get('DIRS', 'tleFile'))


class AsciiColors:
    def __init__(self):
        pass

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


logLineStart = AsciiColors.BOLD + AsciiColors.HEADER + "***>\t" + AsciiColors.ENDC + AsciiColors.OKGREEN
logLineEnd = AsciiColors.ENDC


class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)


def log_cmdline(what, cmdline):
    if config.getboolean("LOG", 'debug'):
        print logLineStart + what + ": '" + " ".join(cmdline) + "'" + logLineEnd

pid = str(os.getpid())
if os.path.isfile(config.get('LOG', 'pid')):
    os.unlink(config.get('LOG', 'pid'))
file(config.get('LOG', 'pid'), 'w').write(pid)

if config.getboolean('LOG', 'enable'):
    sys.stdout = Logger(config.get('LOG', 'filename'))

if config.getboolean('PROCESSING', 'wxQuietOutput'):
    wxQuietOpt = '-q'
else:
    wxQuietOpt = '-C wxQuiet:no'

if config.getboolean('PROCESSING', 'wxDecodeAll'):
    wxDecodeOpt = '-A'
else:
    wxDecodeOpt = '-C wxDecodeAll:no'

if config.getboolean('PROCESSING', 'wxAddTextOverlay'):
    wxAddText = '-k ' + config.get('PROCESSING', 'wxOverlayText') + ' %g %T/%E%p%^%z/e:%e %C'
else:
    wxAddText = '-C wxOther:noOverlay'


# Execution loop declaration
def run_for_duration(cmdline, sleep_for):
    try:
        child = subprocess.Popen(cmdline)
        time.sleep(sleep_for)
        child.terminate()
    except OSError as e:
        print "OS Error during command: " + " ".join(cmdline)
        print "OS Error: " + e.strerror


# FM Recorder definition
def record_fm(frequency, filename, sleep_for, xf_filename):
    print AsciiColors.GRAY
    xf_no_space = xf_filename.replace(" ", "")
    cmdline = ['/usr/bin/rtl_fm',
               '-f', str(frequency),
               '-s', config.getint('SDR', 'sample'),
               '-g', config.getint('SDR', 'gain'),
               '-F', '9',
               '-l', '0',
               '-t', '900',
               '-A', 'fast',
               '-E', 'offset',
               # '-E','pad',
               '-p', config.getint('SDR', 'shift'),
               config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + filename + '.raw']

    log_cmdline("RECORD FM", cmdline)

    run_for_duration(cmdline, sleep_for)


def record_qpsk(sleep_for):
    print AsciiColors.GRAY
    xf_no_space = xfname.replace(" ", "")
    cmdline = [config.get('DIRS', 'system') + '/meteor_qpsk.py', configFile]
    run_for_duration(cmdline, sleep_for)


# Status builder. Crazy shit. These are only examples, do what you want :)
def write_status(frequency, aos_time, los_time, los_time_unix, record_time, xf_name, max_elev, status):
    aos_time_str = strftime('%H:%M:%S', time.localtime(aos_time))
    pass_img_file = strftime('%Y%m%d-%H%M', time.localtime(aos_time)) + '-pass-img.png'
    stat_file = open(config.get('DIRS', 'status'), 'w+')
    if status == 'RECORDING':
        stat_file.write("RECEIVING;yes;" + str(xf_name) +
                        ' AOS@' + str(aos_time_str) + ' LOS@' + str(los_time) +
                        ' REC@' + str(record_time) + 's. max el.@' + str(max_elev) + '°' + ';' +
                        str(xf_name) + '-' + strftime('%Y%m%d-%H%M', time.localtime(aos_time)))

    elif status == 'DECODING':
        stat_file.write('RECEIVING;no;Decoding ' + str(xf_name) + ';' + str(xf_name) +
                        '-' + strftime('%Y%m%d-%H%M', time.localtime(aos_time)))

    elif status == 'WAITING':
        stat_file.write('RECEIVING;no;' + str(xf_name) + ' (AOS@' + str(aos_time_str) + ') @' +
                        str(max_elev) + '° elev. max' + ';' + str(xf_name) +
                        '-' + strftime('%Y%m%d-%H%M', time.localtime(los_time_unix)))

    elif status == 'TOOLOW':
        stat_file.write('RECEIVING;no;' + str(xf_name) +
                        ' (AOS@' + str(aos_time_str) + ') too low (' + str(max_elev) + '°), waiting ' +
                        str(record_time) + 's.')

    stat_file.close()


# Transcoding module
def transcode(filename):
    xf_no_space = xfname.replace(" ", "")
    print logLineStart + 'Transcoding...' + AsciiColors.YELLOW
    cmdlinesox = ['sox',
                  '-t', 'raw',
                  '-r', config.getint('SDR', 'sample'),
                  '-es',
                  '-b', '16',
                  '-c', '1',
                  '-V1',
                  config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + filename + '.raw',
                  config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + filename + '.wav', 'rate',
                  config.getint('SDR', 'wavrate')]

    log_cmdline("SOX", cmdlinesox)

    subprocess.call(cmdlinesox)
    cmdlinetouch = ['touch',
                    '-r' + config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + filename + '.raw',
                    config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + filename + '.wav']

    log_cmdline('SOX TOUCH', cmdlinetouch)

    subprocess.call(cmdlinetouch)
    if config.getboolean('PROCESSING', 'removeRAW'):
        print logLineStart + AsciiColors.ENDC + AsciiColors.RED + 'Removing RAW data' + logLineEnd
        os.remove(config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + filename + '.raw')


def createoverlay(fname, aosTime, satName, recLen):
    print logLineStart + 'Creating Map Overlay...' + logLineEnd
    aosTimeO = int(aosTime) + int('1')
    recLenC = int(recLen)
    # recLenC='2'
    mapfname = os.path.join(config.get('DIRS', 'map'), fname)
    cmdline = ['wxmap',
               '-T', satName,
               '-G', str(config.get('DIRS', 'tle')),
               '-H', str(config.get('DIRS', 'tleFile')),
               '-M', '0',
               '-o',
               '-A', '0',
               '-O', str(recLenC),
               '-L', config.get('QTH', 'lat') + '/' + config.get('QTH', 'lat') + '/' + config.get('QTH', 'alt'),
               str(aosTimeO), mapfname + '-map.png']
    overlay_log = open(mapfname + '-map.png.txt', "w+")

    log_cmdline('CREATE OVERLAY WXMAP', cmdline)

    subprocess.call(cmdline, stderr=overlay_log, stdout=overlay_log)
    overlay_log.close()


def decode_qpsk():
    # TODO write config for decode_meteor.sh
    subprocess.Popen(config.get('DIRS', 'system') + '/decode_meteor.sh')


def decode(fname, aosTime, satName, maxElev, recLen):
    xf_no_space = xfname.replace(" ", "")
    sat_timestamp = int(fname)
    file_name_c = datetime.datetime.fromtimestamp(sat_timestamp).strftime('%Y%m%d-%H%M')

    if config.getboolean('PROCESSING', 'wxAddOverlay'):
        print logLineStart + AsciiColors.OKBLUE + 'Creating overlay map' + logLineEnd
        createoverlay(fname, aosTime, satName, recLen)
        print logLineStart + 'Creating basic image with overlay map' + logLineEnd
        m = open(config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg.txt', "w+")
        m.write('\nSAT: ' + str(xf_no_space) + ', Elevation max: ' + str(maxElev) + ', Date: ' + str(fname) + '\n')
        for psikus in open(config.get('DIRS', 'map') + '/' + str(fname) + '-map.png.txt', "r").readlines():
            res = psikus.replace("\n", " \n")
            m.write(res)
        cmdline = [config.get('DIRS', 'wxInstall') + '/wxtoimg',
                   wxQuietOpt,
                   wxAddText,
                   '-A', '-o', '-R1',
                   '-t', 'NOAA',
                   '-Q ' + config.getint('PROCESSING', 'wxJPEGQuality'),
                   config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                   config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg']
        log_cmdline("DECODE WXTOIMG NORMALMAP", cmdline)
        subprocess.call(cmdline, stderr=m, stdout=m)
        m.close()
        for line in open(config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg.txt',
                         "r").readlines():
            res = line.replace("\n", "")
            res2 = re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
            print logLineStart + AsciiColors.OKBLUE + res2 + logLineEnd
            if "Channel A" in res:
                chan1 = res.rstrip().replace('(', ':').split(':')
                channelA = chan1[1].strip().rstrip()[:1]
            if "Channel B" in res:
                chan1 = res.rstrip().replace('(', ':').split(':')
                channelB = chan1[1].strip().rstrip()[:1]

        # Copy logs
        if config.getboolean('SCP', 'log'):
            print logLineStart + "Sending flight and decode logs..." + AsciiColors.YELLOW
            cmdline_scp_log = ['/usr/bin/scp',
                               config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg.txt',
                               config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':' +
                               config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") +
                               '-' + file_name_c + '-normal-map.jpg.txt']
            log_cmdline("SCP LOG", cmdline_scp_log)
            subprocess.call(cmdline_scp_log)

        if config.getboolean('SCP', 'img'):
            print logLineStart + "Sending base image with map: " + AsciiColors.YELLOW
            cmdline_scp_img = ['/usr/bin/scp',
                               config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg',
                               config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':' +
                               config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") +
                               '-' + file_name_c + '-normal-map.jpg']
            log_cmdline("SCP IMG", cmdline_scp_img)
            subprocess.call(cmdline_scp_img)
            print logLineStart + "Sending OK, go on..." + logLineEnd

        # NEW
        if config.getboolean('PROCESSING', 'wxEnhCreate'):
            print "Channel A:" + channelA + ", Channel B:" + channelB
            for enhancements in config.getlist('PROCESSING', 'wxEnhList'):
                print logLineStart + 'Creating ' + enhancements + ' enhancement image' + logLineEnd
                enhancements_log = open(
                    config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg.txt',
                    "w+")
                enhancements_log.write(
                    '\nEnhancement: ' + enhancements + ', SAT: ' + str(xf_no_space) + ', Elevation max: ' + str(
                        maxElev) + ', Date: ' + str(fname) + '\n')
                if enhancements in ('HVCT', 'HVC'):
                    if channelA in "1" and channelB in "2":
                        print "1 i 2"
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K0', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    elif channelA in "1" and channelB in "1":
                        print "1 i 1 "
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K0', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    elif channelA in "1" and channelB in "4":
                        print "1 i 4 "
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K0', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    elif channelA in "1" and channelB in "3":
                        print "1 i 3"
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K3', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    elif channelA in "2" and channelB in "4":
                        print "2 i 4"
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K1', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    elif channelA in "3" and channelB in "4":
                        print "3 i 4"
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K4', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    else:
                        print "Channel Unknown"
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-K1', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                if enhancements in ('MSA'):
                    if channelA in ("1", "2") and channelB in "4":
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements,
                                                '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                    else:
                        cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                                wxAddText, '-A', '-o', '-c', '-R1',
                                                '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-eNO', '-m',
                                                config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                    'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                         'wxOverlayOffsetY'),
                                                config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                                config.get('DIRS',
                                                           'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                else:
                    cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg', wxQuietOpt, wxDecodeOpt,
                                            wxAddText, '-A', '-o', '-c', '-R1',
                                            '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'), '-e', enhancements, '-m',
                                            config.get('DIRS', 'map') + '/' + fname + '-map.png' + ',' + config.get(
                                                'PROCESSING', 'wxOverlayOffsetX') + ',' + config.get('PROCESSING',
                                                                                                     'wxOverlayOffsetY'),
                                            config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                            config.get('DIRS',
                                                       'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg']
                log_cmdline("ENHANCEMENTS WXTOIMG", cmdline_enhancements)
                subprocess.call(cmdline_enhancements, stderr=enhancements_log, stdout=enhancements_log)

                for psikus in open(config.get('DIRS', 'map') + '/' + str(fname) + '-map.png.txt', "r").readlines():
                    res = psikus.replace("\n", " \n")
                    enhancements_log.write(res)
                enhancements_log.close()

                if config.getboolean('SCP', 'log'):
                    print logLineStart + "Sending " + enhancements + " flight and decode logs..." + AsciiColors.YELLOW
                    cmdline_scp_log = ['/usr/bin/scp',
                                       config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg.txt',
                                       config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':'
                                       + config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") + '-'
                                       + file_name_c + '-' + enhancements + '-map.jpg.txt']
                    log_cmdline("SCP LOG", cmdline_scp_log)
                    subprocess.call(cmdline_scp_log)
                    print logLineStart + "Sending logs OK, moving on..." + logLineEnd

                if config.getboolean('SCP', 'img'):
                    print logLineStart + "Sending " + enhancements + " image with overlay map... " + AsciiColors.YELLOW
                    cmdline_scp_img = ['/usr/bin/scp', config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg',
                                       config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':'
                                       + config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") + '-'
                                       + file_name_c + '-' + enhancements + '-map.jpg']
                    log_cmdline("SCP IMG", cmdline_scp_img)
                    subprocess.call(cmdline_scp_img)
                    print logLineStart + "Send image OK, moving on..." + logLineEnd

        # SFPG
        if config.getboolean('SCP', 'sfpgLink'):
            path_plik = config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-MCIR-precip-map.jpg'
            path_plik2 = config.get('DIRS', 'img') + '/' + satName + '/_image.jpg'
            if os.path.isfile(path_plik2):
                os.unlink(path_plik2)
            os.symlink(path_plik, path_plik2)
    else:
        print logLineStart + 'Creating basic image without map' + logLineEnd
        r = open(config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal.jpg.txt', "w+")
        cmdline = [config.get('DIRS', 'wxInstall') + '/wxtoimg',
                   wxQuietOpt, wxDecodeOpt, wxAddText,
                   '-o', '-R1',
                   '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'),
                   '-t', 'NOAA',
                   config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                   config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal.jpg']
        log_cmdline("WXTOIMG", cmdline)
        r.write('\nSAT: ' + str(xf_no_space) + ', Elevation max: ' + str(maxElev) + ', Date: ' + str(fname) + '\n')
        subprocess.call(cmdline, stderr=r, stdout=r)
        r.close()

        for line in open(config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal.jpg.txt',
                         "r").readlines():
            res = line.replace("\n", "")
            res2 = re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
            print logLineStart + AsciiColors.OKBLUE + res2 + logLineEnd

        if config.getboolean('SCP', 'log'):
            print logLineStart + "Sending flight and decode logs..." + AsciiColors.YELLOW
            cmdline_scp_log = ['/usr/bin/scp',
                               config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg.txt',
                               config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':'
                               + config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") +
                               '-' + file_name_c + '-normal-map.jpg.txt']
            log_cmdline("SCP LOG", cmdline_scp_log)
            subprocess.call(cmdline_scp_log)

        if config.getboolean('SCP', 'img'):
            print logLineStart + "Sending base image with map: " + AsciiColors.YELLOW
            cmdline_scp_img = ['/usr/bin/scp',
                               config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-normal-map.jpg',
                               config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':'
                               + config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") + '-'
                               + file_name_c + '-normal-map.jpg']
            log_cmdline("SCP IMG", cmdline_scp_img)
            subprocess.call(cmdline_scp_img)
            print logLineStart + "Sending OK, go on..." + logLineEnd

        if config.getboolean('PROCESSING', 'wxEnhCreate'):
            for enhancements in config.getlist('PROCESSING', 'wxEnhList'):
                print logLineStart + 'Creating ' + enhancements + ' image' + logLineEnd
                enhancements_log = open(
                    config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-nomap.jpg.txt',
                    "w+")
                enhancements_log.write(
                    '\nEnhancement: ' + enhancements + ', SAT: ' + str(xf_no_space) + ', Elevation max: ' + str(
                        maxElev) + ', Date: ' + str(fname) + '\n')
                cmdline_enhancements = [config.get('DIRS', 'wxInstall') + '/wxtoimg',
                                        wxQuietOpt, wxDecodeOpt, wxAddText,
                                        '-o', '-K', '-R1',
                                        '-Q ' + config.get('PROCESSING', 'wxJPEGQuality'),
                                        '-e', enhancements,
                                        config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + fname + '.wav',
                                        config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-nomap.jpg']
                log_cmdline("WXTOIMG ENHANCEMENTS", cmdline_enhancements)
                subprocess.call(cmdline_enhancements, stderr=enhancements_log, stdout=enhancements_log)
                enhancements_log.close()

                if config.getboolean('SCP', 'log'):
                    print logLineStart + "Sending " + enhancements + " flight and decode logs..." + AsciiColors.YELLOW
                    cmdline_scp_log = ['/usr/bin/scp', config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg.txt',
                                       config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':'
                                       + config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") + '-'
                                       + file_name_c + '-' + enhancements + '-map.jpg.txt']
                    log_cmdline("SCP LOG", cmdline_scp_log)
                    subprocess.call(cmdline_scp_log)

                if config.getboolean('SCP', 'img'):
                    print logLineStart + "Sending " + enhancements + " image with overlay map... " + AsciiColors.YELLOW
                    cmdline_scp_img = ['/usr/bin/scp', config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-' + enhancements + '-map.jpg',
                                       config.get('SCP', 'user') + '@' + config.get('SCP', 'host') + ':'
                                       + config.get('SCP', 'dir') + '/' + satName.replace(" ", "\ ") + '-'
                                       + file_name_c + '-' + enhancements + '-map.jpg']
                    log_cmdline("SCP IMG", cmdline_scp_img)
                    subprocess.call(cmdline_scp_img)
                    print logLineStart + "Sending OK, moving on" + logLineEnd

        if config.getboolean('SCP', 'sfpgLink'):
            path_plik = config.get('DIRS', 'img') + '/' + satName + '/' + file_name_c + '-MCIR-precip-nomap.jpg'
            path_plik2 = config.get('DIRS', 'img') + '/' + satName + '/_image.jpg'
            if os.path.isfile(path_plik2):
                os.unlink(path_plik2)
            os.symlink(path_plik, path_plik2)


# Record and transcode wave file
def record_wav(frequency, filename, sleep_for, xfilename):
    record_fm(frequency, filename, sleep_for, xfilename)
    transcode(filename)
    if config.getboolean('PROCESSING', 'createSpectro'):
        spectrum(filename)


def spectrum(xfilename):
    xf_no_space = xfname.replace(" ", "")
    print logLineStart + 'Creating flight spectrum' + logLineEnd
    cmdline = ['sox',
               config.get('DIRS', 'rec') + '/' + xf_no_space + '-' + xfilename + '.wav',
               '-n', 'spectrogram',
               '-o', config.get('DIRS', 'spec') + '/' + xf_no_space + '-' + xfilename + '.png']
    log_cmdline("SOX SPECTRUM", cmdline)
    subprocess.call(cmdline)


def find_next_pass():
    predictions = [
        pypredict.aoslos(s, config.get('QTH', 'minElev'), config.get('QTH', 'minElevMeteor'), config.get('QTH', 'lat'),
                         config.get('QTH', 'lon'), config.get('QTH', 'alt'), tleFileDir) for s in
        config.getlist('BIRDS', 'satellites')]
    aoses = [p[0] for p in predictions]
    next_index = aoses.index(min(aoses))
    return (config.getlist('BIRDS', 'satellites')[next_index],
            config.getlist('BIRDS', 'freqs')[next_index],
            predictions[next_index])


# Now magic
while True:
    (satName, freq, (aosTime, losTime, duration, maxElev)) = find_next_pass()
    now = time.time()
    towait = aosTime - now

    aosTimeCnv = strftime('%H:%M:%S', time.localtime(aosTime))
    emergeTimeUtc = strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(aosTime))
    losTimeCnv = strftime('%H:%M:%S', time.localtime(losTime))
    dimTimeUtc = strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(losTime))

    # OK, now we have to decide what if recording or sleeping
    if towait > 0:
        print logLineStart + "waiting " + AsciiColors.CYAN + str(towait).split(".")[
            0] + AsciiColors.OKGREEN + " seconds  (" + AsciiColors.CYAN + aosTimeCnv + AsciiColors.OKGREEN + " to " + AsciiColors.CYAN + losTimeCnv + ", " + str(
            duration) + AsciiColors.OKGREEN + "s.) for " + AsciiColors.YELLOW + satName + AsciiColors.OKGREEN + " @ " + AsciiColors.CYAN + str(
            maxElev) + AsciiColors.OKGREEN + "° el. " + logLineEnd
        write_status(freq, aosTime, losTimeCnv, aosTime, towait, satName, maxElev, 'WAITING')
        time.sleep(towait)

    if aosTime < now:
        recordTime = losTime - now
        if recordTime < 1:
            recordTime = 1
    elif aosTime >= now:
        recordTime = duration
        if recordTime < 1:
            recordTime = 1
            ##
    fname = str(aosTime)
    xfname = satName
    print logLineStart + "Beginning pass of " + AsciiColors.YELLOW + satName + AsciiColors.OKGREEN + " at " + AsciiColors.CYAN + str(
        maxElev) + "°" + AsciiColors.OKGREEN + " elev.\n" + logLineStart + "Predicted start " + AsciiColors.CYAN + aosTimeCnv + AsciiColors.OKGREEN + " and end " + AsciiColors.CYAN + losTimeCnv + AsciiColors.OKGREEN + ".\n" + logLineStart + "Will record for " + AsciiColors.CYAN + \
          str(recordTime).split(".")[0] + AsciiColors.OKGREEN + " seconds." + logLineEnd
    write_status(freq, aosTime, losTimeCnv, str(losTime), str(recordTime).split(".")[0], satName, maxElev, 'RECORDING')

    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
        record_wav(freq, fname, recordTime, xfname)
    elif xfname == 'METEOR-M 2':
        record_qpsk(recordTime)
    print logLineStart + "Decoding data" + logLineEnd
    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
        write_status(freq, aosTime, losTimeCnv, str(losTime), str(recordTime).split(".")[0], satName, maxElev,
                     'DECODING')
        decode(fname, aosTime, satName, maxElev, recordTime)  # make picture
    elif xfname == 'METEOR-M 2':
        if config.getboolean('PROCESSING', 'decodeMeteor'):
            print "This may take a loooong time and is resource hungry!!!"
            write_status(freq, aosTime, losTimeCnv, str(losTime), str(recordTime).split(".")[0], satName, maxElev,
                         'DECODING')
            decode_qpsk()
    print logLineStart + "Finished pass of " + AsciiColors.YELLOW + satName + AsciiColors.OKGREEN + " at " + AsciiColors.CYAN + losTimeCnv + AsciiColors.OKGREEN + ". Sleeping for" + AsciiColors.CYAN + " 10" + AsciiColors.OKGREEN + " seconds" + logLineEnd
    time.sleep(10.0)
