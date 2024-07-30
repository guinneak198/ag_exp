"""Zoom out to about 10 us timescale on GDS, and 100 mV. Acquire mode should be Hi resolution and trigger should be set to normal
"""
import pyspecdata as psd
import os
import SpinCore_pp as spc
from datetime import datetime
from Instruments import GDS_scope
import numpy as np
tx_phases = r_[0.0,90.0,180.0,270.0]
nPhaseSteps = 1
my_exp_type = "test_equipment"
assert os.path.exists(psd.getDATADIR(exp_type=my_exp_type))
config_dict = spc.configuration("active.ini")
(nPoints,config_dict["SW_kHz"],config_dict["acq_time_ms"]) = spc.get_integer_sampling_intervals(
        config_dict["SW_kHz"],config_dict["acq_time_ms"])
config_dict["type"] = "pulse_capture"
config_dict["date"]=datetime.now().strftime('%y%m%d')
config_dict["misc_counter"] += 1
sqrt_P = config_dict["amplitude"] * np.sqrt(75)
desired_beta = 38
prog_beta = spc.prog_plen(desired_beta)
prog_beta180 = spc.prog_plen(2*desired_beta)
p90 = prog_beta / sqrt_P
prog_p90_us = prog_beta /sqrt_P
prog_p180_us = prog_beta180 / sqrt_P
print("sending in a p90 of %g to get a programmed beta of %g which will produce
        the desired beta of %g"%(prog_p90_us,prog_beta,desired_beta))
print("sending in a p180 of %g to get a programmed beta of %g"%(prog_p180_us,prog_beta180))
input("look okay"?)
datalist = []
for index in range(5):
    print("***")
    print("INDEX %d"%index)
    print("***")
    spc.configureTX(config_dict["adc_Offset"], config_dict["carrierFreq_MHz"], tx_phases, config_dict["amplitude"], nPoints)
    acq_time = spc.configureRX(config_dict["SW_kHz"], nPoints, 1, 1, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    spc.init_ppg();
    spc.load([
        ('marker','thisstart',1),
        ('phase_reset',1),
        ('delay_TTL',1.0),
        ('pulse_TTL',prog_p90_us,0),
        ('delay',config_dict["tau_us"]),
        ('delay_TTL',1.0),
        ('pulse_TTL',prog_p180_us,0),
        ('delay',config_dict["deadtime_us"]),
        ('acquire',acq_time),
        ('delay',config_dict["repetition_us"]),
        ('jumpto','thisstart'),
        ])
    spc.stop_ppg();
    spc.runBoard();
    datalist = []
    with GDS_scope() as g:
        for j in range(1,6):
            print("TRYING TO GRAB WAVEFORM")
            datalist.append(g.waveform(ch=2))
        print("GOT WAVEFORM")
        capture_data = psdconcat(datalist,'ch').reorder('t')
    spc.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
s = capture_data['ch',0]
s.set_units('t','s')
s.set_prop("set_p90", prog_p90_us)
s.set_prop("set_p180", prog_p180_us)
s.set_prop("set_beta", prog_beta)
s.set_prop("set_beta180",prog_beta180)
with psd.figlist_var() as fl:
    fl.next('sequence')
    fl.plot(s)
config_dict = spc.save_data(s, my_exp_type, config_dict,"misc")
config_dict.write()
