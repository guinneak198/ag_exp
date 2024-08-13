"""Zoom out to about 10 us timescale on GDS, and 100 mV. Acquire mode should be Hi resolution and trigger should be set to normal
"""
from pyspecdata import *
from Instruments import *
import SpinCore_pp
from SpinCore_pp import prog_plen, configuration, get_integer_sampling_intervals
# {{{ importing acquisition parameters
config_dict = configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = get_integer_sampling_intervals(
    config_dict["SW_kHz"], config_dict["acq_time_ms"]
)
# }}}
# {{{ parameters
tx_phases = r_[0.0,90.0,180.0,270.0]
prog_p90_us = prog_plen(config_dict['beta_90_s_sqrtW'], config_dict['amplitude'])

SpinCore_pp.configureTX(config_dict['adc_offset'], config_dict['carrierFreq_MHz'], tx_phases, config_dict['amplitude'], nPoints)
acq_time = SpinCore_pp.configureRX(config_dict['SW_kHz'], nPoints, config_dict['nScans'], config_dict['nEchoes'], 1) #ms
SpinCore_pp.init_ppg();
SpinCore_pp.load([
    ('phase_reset',1),
    ('delay_TTL',1.0),
    ('pulse_TTL',prog_p90_us,0),
    ('delay',config_dict['deadtime_us']),
    ])
SpinCore_pp.stop_ppg();
SpinCore_pp.runBoard();
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
