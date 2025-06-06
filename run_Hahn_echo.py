"""
Spin Echo
=========

To run this experiment, please open Xepr on the EPR computer, connect to
spectrometer, load the experiment 'set_field' and enable XEPR API. Then, in a
separate terminal, run the program XEPR_API_server.py, and wait for it to
tell you 'I am listening' - then, you should be able to run this program from
the NMR computer to set the field etc. 
"""

from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp import get_integer_sampling_intervals, save_data
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
fl = figlist_var()
my_exp_type = "ODNP_NMR_comp/Echoes"
assert os.path.exists(getDATADIR(exp_type=my_exp_type))
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = get_integer_sampling_intervals(
    SW_kHz=config_dict["SW_kHz"],
    time_per_segment_ms=config_dict["acq_time_ms"],
)
#}}}
#{{{create filename and save to config file
config_dict['type'] = 'echo'
config_dict['date'] = datetime.now().strftime('%y%m%d')
config_dict['echo_counter'] += 1
#}}}
# {{{set phase cycling
# default phase cycling of run_spin_echo is to use a 4 step on the 90 pulse
# so this is here just for setting the chunked axis later and calculating the
# total points
ph1_cyc = r_[0, 1, 2, 3]
nPhaseSteps = 4
# }}}
input(
    "I'm assuming that you've tuned your probe to %f since that's what's in your .ini file. Hit enter if this is true"
    % config_dict["carrierFreq_MHz"]
)

Field = config_dict['carrierFreq_MHz']/config_dict['gamma_eff_MHz_G']
print(
        "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
        %Field
        )
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
    print("field set to ",Field)
#}}}
#{{{check total points
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14,  "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}

#{{{acquire echo

data = run_spin_echo(
    nScans=config_dict['nScans'],
    indirect_idx = 0,
    indirect_len = 1,
    ph1_cyc = ph1_cyc,
    amplitude = config_dict["amplitude"],
    adcOffset = config_dict['adc_offset'],
    deblank_us=config_dict["deblank_us"],
    carrierFreq_MHz = config_dict['carrierFreq_MHz'],
    nPoints = nPoints,
    nEchoes = 1,
    plen = config_dict['beta_90_s_sqrtW'],
    repetition_us = config_dict['repetition_us'],
    tau_us = config_dict['tau_us'],
    SW_kHz = config_dict['SW_kHz'],
    ret_data = None)
#}}}
# {{{ chunk and save data
data.chunk(
    "t",
    ["ph1", "t2"],
    [len(ph1_cyc), -1],
)
data.setaxis("ph1", ph1_cyc / 4)
data.reorder(["ph1", "nScans", "t2"])
data.set_prop("postproc_type", "spincore_generalproc_v1")
data.set_units("t2", "s")
data.set_prop("coherence_pathway", {"ph1": 1})
data.set_prop("acq_params", config_dict.asdict())
#{{{Look at raw data
fl.next('image')
fl.image(data.C.mean('nScans'))
#}}}    
config_dict = save_data(data, my_exp_type, config_dict, "echo")
config_dict.write()
data.ft('t2',shift=True)
fl.next('image - ft')
fl.image(data.C.mean('nScans'))
fl.next('image - ft, coherence')
data.ft(['ph1'])
fl.image(data.C.mean('nScans'))
fl.next('data plot')
data_slice = data['ph1',1].C.mean('nScans')
fl.plot(data_slice, alpha=0.5)
fl.plot(data_slice.imag, alpha=0.5)
fl.plot(abs(data_slice), color='k', alpha=0.5)
fl.show()
