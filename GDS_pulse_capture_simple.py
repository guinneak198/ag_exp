"""Zoom out to about 10 us timescale on GDS, and 100 mV. Acquire mode should be Hi resolution and trigger should be set to normal
"""
from pyspecdata import *
from Instruments import *
import SpinCore_pp
from SpinCore_pp import prog_plen
adcOffset = 45
carrierFreq_MHz = 14.89
# {{{ parameters
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 1
nEchoes = 1
nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
deadtime = 10.0
repetition = 0.25e6
SW_kHz = 0.9#50.0
nPoints = 2048#int(aq/SW_kHz+0.5)#1024*2
acq_time = nPoints/SW_kHz # ms
# }}}
tau = 100
p90 = 250#us
prog_p90_us = prog_plen(p90)
prog_p180_us = prog_plen(2*p90)
amplitude = 0.004 #full power

SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
SpinCore_pp.init_ppg();
SpinCore_pp.load([
    ('marker','thisstart',1),
    ('phase_reset',1),
    ('delay_TTL',1.0),
    ('pulse_TTL',p90,0),
    ('delay',tau),
    ('delay_TTL',1.0),
    ('pulse_TTL',2*p90,0),
    ('delay',deadtime),
    ('acquire',acq_time),
    ('delay',repetition),
    ('jumpto','thisstart'),
    ])
SpinCore_pp.stop_ppg();
SpinCore_pp.runBoard();
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
