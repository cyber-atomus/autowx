#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Meteor QPSK LRPT NOGUI DOOPLER IN 
# Author: otti i at
# Generated: Thu Mar 16 19:02:08 2017
##################################################

from datetime import datetime
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import osmosdr
import os
import os, shutil
import sys

bitstream_dir = '/opt/wxsat/rec'
lrpt_dir = '/opt/wxsat/lrpt/'

bitstream_file = "meteor_LRPT_" + datetime.now().strftime("%d%m%Y_%H%M") + ".s"
bitstream_name = bitstream_dir+"meteor_LRPT_" + datetime.now().strftime("%d%m%Y_%H%M") + ".s"

rgb_lrpt_file = lrpt_dir+"rgb.ini"
mono_lrpt_file = lrpt_dir+"mono.ini"

#Remember to unescape backslashes!!!
BITSTREAM_WINDOWS_DIR="D:\\"
IMAGES_WINDOWS_DIR="D:\\lrp\\"

class create_lrpt_config():
    def __init__(self):
	if os.path.isfile(rgb_lrpt_file):
	    os.unlink(rgb_lrpt_file)
	l=open(rgb_lrpt_file,'w+')
	l.write("[IN]\r\n")
	l.write("source=file\r\n")
	l.write("filename="+BITSTREAM_WINDOWS_DIR+bitstream_file+"\r\n")
	l.write("mode=72K\r\n")
	l.write("[OUT]\r\n")
	l.write("rgb=122.jpg\r\n")
	l.write("rgb_q=100\r\n")
#	l.write("mono=jpg\r\n")
	l.write("logs=no\r\n")
	l.write("APID70=no\r\n")
	l.write("VCDU=no\r\n")
	l.write("path="+IMAGES_WINDOWS_DIR+"\r\n")
	l.write("[GEO]\r\n")
	l.write("RoughStartTimeUTC="+datetime.now().strftime("%d.%m.%Y")+"\r\n")
	l.write("TleFileName="+BITSTREAM_WINDOWS_DIR+"m2.txt\r\n")
	l.close

	if os.path.isfile(mono_lrpt_file):
	    os.unlink(mono_lrpt_file)
	m=open(mono_lrpt_file,'w+')
	m.write("[IN]\r\n")
	m.write("source=file\r\n")
	m.write("filename="+BITSTREAM_WINDOWS_DIR+bitstream_file+"\r\n")
	m.write("mode=72K\r\n")
	m.write("[OUT]\r\n")
	m.write("rgb=555.jpg\r\n")
	m.write("rgb_q=100\r\n")
	m.write("mono=jpg\r\n")
	m.write("logs=no\r\n")
	m.write("APID70=no\r\n")
	m.write("VCDU=no\r\n")
	m.write("path="+IMAGES_WINDOWS_DIR+"\r\n")
	l.write("[GEO]\r\n")
	l.write("RoughStartTimeUTC="+datetime.now().strftime("%d.%m.%Y")+"\r\n")
	l.write("TleFileName="+BITSTREAM_WINDOWS_DIR+"m2.txt\r\n")
	m.close

class atomus_meteor_nogui(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Meteor QPSK LRPT NOGUI DOOPLER IN ")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate_airspy = samp_rate_airspy = 1406250
        self.decim = decim = 9
        self.symb_rate = symb_rate = 72000
        self.samp_rate = samp_rate = samp_rate_airspy/decim
        self.sps = sps = (samp_rate*1.0)/(symb_rate*1.0)
        self.rfgain_static = rfgain_static = 48
        self.ppm_r = ppm_r = 63
        self.pll_alpha_static = pll_alpha_static = 0.001
        self.ifgain_static = ifgain_static = 48
        self.freq = freq = 137900000
        self.clock_alpha_static = clock_alpha_static = 0.001
        self.bitstream_name = bitstream_name

        ##################################################
        # Blocks
        ##################################################
        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.rtlsdr_source_0.set_sample_rate(samp_rate_airspy)
        self.rtlsdr_source_0.set_center_freq(freq, 0)
        self.rtlsdr_source_0.set_freq_corr(ppm_r, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(rfgain_static, 0)
        self.rtlsdr_source_0.set_if_gain(ifgain_static, 0)
        self.rtlsdr_source_0.set_bb_gain(10, 0)
        self.rtlsdr_source_0.set_antenna("", 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)
          
        self.root_raised_cosine_filter_0 = filter.fir_filter_ccf(1, firdes.root_raised_cosine(
        	1, samp_rate, symb_rate, 0.6, 361))
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=decim,
                taps=None,
                fractional_bw=None,
        )
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(pll_alpha_static, 4)
        self.digital_constellation_soft_decoder_cf_1 = digital.constellation_soft_decoder_cf(digital.constellation_calcdist(([-1-1j, -1+1j, 1+1j, 1-1j]), ([0, 1, 3, 2]), 4, 1).base())
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_cc(sps, clock_alpha_static**2/4.0, 0.5, clock_alpha_static, 0.005)
        self.blocks_float_to_char_0 = blocks.float_to_char(1, 127)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, bitstream_name, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.analog_rail_ff_0 = analog.rail_ff(-1, 1)
        self.analog_agc_xx_0 = analog.agc_cc(1000e-4, 0.5, 1.0)
        self.analog_agc_xx_0.set_max_gain(4000)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_agc_xx_0, 0), (self.root_raised_cosine_filter_0, 0))
        self.connect((self.analog_rail_ff_0, 0), (self.blocks_float_to_char_0, 0))
        self.connect((self.blocks_float_to_char_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.digital_constellation_soft_decoder_cf_1, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_1, 0), (self.analog_rail_ff_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.analog_agc_xx_0, 0))
        self.connect((self.root_raised_cosine_filter_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.rational_resampler_xxx_0, 0))



    def get_samp_rate_airspy(self):
        return self.samp_rate_airspy

    def set_samp_rate_airspy(self, samp_rate_airspy):
        self.samp_rate_airspy = samp_rate_airspy
        self.set_samp_rate(self.samp_rate_airspy/self.decim)
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate_airspy)

    def get_decim(self):
        return self.decim

    def set_decim(self, decim):
        self.decim = decim
        self.set_samp_rate(self.samp_rate_airspy/self.decim)

    def get_symb_rate(self):
        return self.symb_rate

    def set_symb_rate(self, symb_rate):
        self.symb_rate = symb_rate
        self.set_sps((self.samp_rate*1.0)/(self.symb_rate*1.0))
        self.root_raised_cosine_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, self.symb_rate, 0.6, 361))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_sps((self.samp_rate*1.0)/(self.symb_rate*1.0))
        self.root_raised_cosine_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, self.symb_rate, 0.6, 361))

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.digital_clock_recovery_mm_xx_0.set_omega(self.sps)

    def get_rfgain_static(self):
        return self.rfgain_static

    def set_rfgain_static(self, rfgain_static):
        self.rfgain_static = rfgain_static
        self.rtlsdr_source_0.set_gain(self.rfgain_static, 0)

    def get_ppm_r(self):
        return self.ppm_r

    def set_ppm_r(self, ppm_r):
        self.ppm_r = ppm_r
        self.rtlsdr_source_0.set_freq_corr(self.ppm_r, 0)

    def get_pll_alpha_static(self):
        return self.pll_alpha_static

    def set_pll_alpha_static(self, pll_alpha_static):
        self.pll_alpha_static = pll_alpha_static
        self.digital_costas_loop_cc_0.set_loop_bandwidth(self.pll_alpha_static)

    def get_ifgain_static(self):
        return self.ifgain_static

    def set_ifgain_static(self, ifgain_static):
        self.ifgain_static = ifgain_static
        self.rtlsdr_source_0.set_if_gain(self.ifgain_static, 0)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.rtlsdr_source_0.set_center_freq(self.freq, 0)

    def get_clock_alpha_static(self):
        return self.clock_alpha_static

    def set_clock_alpha_static(self, clock_alpha_static):
        self.clock_alpha_static = clock_alpha_static
        self.digital_clock_recovery_mm_xx_0.set_gain_omega(self.clock_alpha_static**2/4.0)
        self.digital_clock_recovery_mm_xx_0.set_gain_mu(self.clock_alpha_static)

    def get_bitstream_name(self):
        return self.bitstream_name

    def set_bitstream_name(self, bitstream_name):
        self.bitstream_name = bitstream_name
        self.blocks_file_sink_0.open(self.bitstream_name)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = atomus_meteor_nogui()
    cr = create_lrpt_config()
    print bitstream_name
    tb.start()
    tb.wait()
