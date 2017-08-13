#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Meteor QPSK soft-division generator
# Author: at
# Description: This file will receive Meteor MN2 using RTL-SDR and will create 72k soft-division file.
# It has no GUI. Ctrl+C or something like that kills the program. Based on original by otti.
# Generated: Fri Apr  7 07:15:12 2017
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
import sys
import cfg

configFile = 'autowx.ini'

if len(sys.argv) > 2:
    print("Usage: {} [autowx.ini]".format(sys.argv[0]))
    exit(-1)
elif len(sys.argv) == 2:
    configFile = sys.argv[1]

config = cfg.get(configFile)

bitstream_file = "meteor_LRPT_" + datetime.now().strftime("%d%m%Y_%H%M") + ".s"
bitstream_name = config.get('METEOR', 'bitstreams') + "meteor_LRPT_" + datetime.now().strftime("%d%m%Y_%H%M") + ".s"
image_name = config.get('METEOR', 'imgs') + "meteor_LRPT_" + datetime.now().strftime("%d%m%Y_%H%M") + ".125"

rgb_lrpt_file = config.get('METEOR', 'lrpts') + "rgb.ini"
mono_lrpt_file = config.get('METEOR', 'lrpts') + "mono.ini"

# Remember to unescape backslashes!!!
BITSTREAM_WINDOWS_DIR = "D:\\"
IMAGES_WINDOWS_DIR = "D:\\lrp\\"


class CreateLrptConfig:
    def __init__(self):
        if os.path.isfile(rgb_lrpt_file):
            os.unlink(rgb_lrpt_file)
        l = open(rgb_lrpt_file, 'w+')
        l.write("[IN]\r\n")
        l.write("source=file\r\n")
        l.write("filename=" + BITSTREAM_WINDOWS_DIR + bitstream_file + "\r\n")
        l.write("mode=72K\r\n")
        l.write("[OUT]\r\n")
        l.write("rgb=122.jpg\r\n")
        l.write("rgb_q=100\r\n")
        # l.write("mono=jpg\r\n")
        l.write("logs=no\r\n")
        l.write("APID70=no\r\n")
        l.write("VCDU=no\r\n")
        l.write("path=" + IMAGES_WINDOWS_DIR + "\r\n")
        l.close()

        if os.path.isfile(mono_lrpt_file):
            os.unlink(mono_lrpt_file)
        m = open(mono_lrpt_file, 'w+')
        m.write("[IN]\r\n")
        m.write("source=file\r\n")
        m.write("filename=" + BITSTREAM_WINDOWS_DIR + bitstream_file + "\r\n")
        m.write("mode=72K\r\n")
        m.write("[OUT]\r\n")
        m.write("rgb=555.jpg\r\n")
        m.write("rgb_q=100\r\n")
        m.write("mono=jpg\r\n")
        m.write("logs=no\r\n")
        m.write("APID70=no\r\n")
        m.write("VCDU=no\r\n")
        m.write("path=" + IMAGES_WINDOWS_DIR + "\r\n")
        m.close()

        if os.path.isfile(config.get('METEOR', 'decode_script')):
            os.unlink(config.get('METEOR', 'decode_script'))
        g = open(config.get('METEOR', 'decode_script'), 'w+')
        g.write("#!/bin/bash\n")
        g.write("\n")
        g.write("/usr/local/bin/medet " + bitstream_name + " " + image_name + " -t >/tmp/METEOR_DECODE.log 2>&1\n")
        # g.write("convert -quality 97 "+image_name+".bmp "+image_name+".jpg")
        g.write("\n")
        g.close()

        os.chmod(config.get('METEOR', 'decode_script'), 0755)


class MeteorQpsk(gr.top_block):
    def __init__(self, ppm=36):
        gr.top_block.__init__(self, "Meteor QPSK soft-division generator")

        ##################################################
        # Parameters
        ##################################################
        self.ppm = ppm

        ##################################################
        # Variables
        ##################################################
        self.samp_rate_rtl = samp_rate_rtl = 1250000
        self.decim = decim = 8
        self.symb_rate = symb_rate = 72000
        self.samp_rate = samp_rate = samp_rate_rtl / decim
        self.output_dir = output_dir = config.get('METEOR', 'bitstreams')
        self.sps = sps = (samp_rate * 1.0) / (symb_rate * 1.0)
        self.rfgain_static = rfgain_static = 39
        self.ppm_static = ppm_static = 32
        self.pll_alpha_static = pll_alpha_static = 0.015
        self.ifgain_static = ifgain_static = 39
        self.freq = freq = 137900000
        self.clock_alpha_static = clock_alpha_static = 0.001
        self.bitstream_name = bitstream_name

        ##################################################
        # Blocks
        ##################################################
        self.rtlsdr_source_0 = osmosdr.source(args="numchan=" + str(1) + " " + '')
        self.rtlsdr_source_0.set_sample_rate(samp_rate_rtl)
        self.rtlsdr_source_0.set_center_freq(freq, 0)
        self.rtlsdr_source_0.set_freq_corr(ppm_static, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(rfgain_static, 0)
        self.rtlsdr_source_0.set_if_gain(ifgain_static, 0)
        self.rtlsdr_source_0.set_bb_gain(10, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
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
        self.digital_constellation_soft_decoder_cf_1 = digital.constellation_soft_decoder_cf(
            digital.constellation_calcdist(([-1 - 1j, -1 + 1j, 1 + 1j, 1 - 1j]), ([0, 1, 3, 2]), 4, 1).base())
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_cc(sps, clock_alpha_static ** 2 / 4.0, 0.5,
                                                                           clock_alpha_static, 0.005)
        self.blocks_float_to_char_0 = blocks.float_to_char(1, 127)
        self.bitstream_name_out = blocks.file_sink(gr.sizeof_char * 1, bitstream_name, False)
        self.bitstream_name_out.set_unbuffered(False)
        self.analog_rail_ff_0 = analog.rail_ff(-1, 1)
        self.analog_agc_xx_0 = analog.agc_cc(1000e-4, 0.5, 1.0)
        self.analog_agc_xx_0.set_max_gain(4000)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_agc_xx_0, 0), (self.root_raised_cosine_filter_0, 0))
        self.connect((self.analog_rail_ff_0, 0), (self.blocks_float_to_char_0, 0))
        self.connect((self.blocks_float_to_char_0, 0), (self.bitstream_name_out, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.digital_constellation_soft_decoder_cf_1, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_1, 0), (self.analog_rail_ff_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.analog_agc_xx_0, 0))
        self.connect((self.root_raised_cosine_filter_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.rational_resampler_xxx_0, 0))

    def get_ppm(self):
        return self.ppm

    def set_ppm(self, ppm):
        self.ppm = ppm

    def get_samp_rate_rtl(self):
        return self.samp_rate_rtl

    def set_samp_rate_rtl(self, samp_rate_rtl):
        self.samp_rate_rtl = samp_rate_rtl
        self.set_samp_rate(self.samp_rate_rtl / self.decim)
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate_rtl)

    def get_decim(self):
        return self.decim

    def set_decim(self, decim):
        self.decim = decim
        self.set_samp_rate(self.samp_rate_rtl / self.decim)

    def get_symb_rate(self):
        return self.symb_rate

    def set_symb_rate(self, symb_rate):
        self.symb_rate = symb_rate
        self.set_sps((self.samp_rate * 1.0) / (self.symb_rate * 1.0))
        self.root_raised_cosine_filter_0.set_taps(
            firdes.root_raised_cosine(1, self.samp_rate, self.symb_rate, 0.6, 361))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_sps((self.samp_rate * 1.0) / (self.symb_rate * 1.0))
        self.root_raised_cosine_filter_0.set_taps(
            firdes.root_raised_cosine(1, self.samp_rate, self.symb_rate, 0.6, 361))

    def get_output_dir(self):
        return self.output_dir

    def set_output_dir(self, output_dir):
        self.output_dir = output_dir
        self.set_bitstream_name(self.output_dir + "meteor_LRPT_" + datetime.now().strftime("%d%m%Y_%H%M") + ".s")

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

    def get_ppm_static(self):
        return self.ppm_static

    def set_ppm_static(self, ppm_static):
        self.ppm_static = ppm_static
        self.rtlsdr_source_0.set_freq_corr(self.ppm_static, 0)

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
        self.digital_clock_recovery_mm_xx_0.set_gain_omega(self.clock_alpha_static ** 2 / 4.0)
        self.digital_clock_recovery_mm_xx_0.set_gain_mu(self.clock_alpha_static)

    def get_bitstream_name(self):
        return self.bitstream_name

    def set_bitstream_name(self, bs_name):
        self.bitstream_name = bs_name
        self.bitstream_name_out.open(self.bitstream_name)


def argument_parser():
    description = 'This file will receive Meteor MN2 using RTL-SDR and will create 72k soft-division file. ' \
                  'It has no GUI. Ctrl+C or something like that kills the program. Based on original by otti.'
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option, description=description)
    parser.add_option(
        "", "--ppm", dest="ppm", type="intx", default=63,
        help="Set rtl_ppm [default=%default]")
    return parser


def main(top_block_cls=MeteorQpsk, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable real-time scheduling."

    tb = top_block_cls(ppm=options.ppm)
    cr = CreateLrptConfig()
    print bitstream_name
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
