from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
from SpinCore_pp.ppg import run_spin_echo
from SpinCore_pp import prog_plen
import logging
fl = figlist_var()
#{{{Parameters that change for new samples
output_name = '200uM_TEMPOL_nutation_1'
adcOffset = 57
carrierFreq_MHz = 14.8931467392
nScans = 4
nEchoes = 1
repetition = 10e6
p90_range = linspace(1,15,5,endpoint=False)
SW_kHz = 3.9 #24.0 originally
acq_time = 1024.
tau_us = 5000
#}}}
ph1_cyc = r_[0,1,2,3]
#{{{These should stay the same regardless of sample
date = datetime.now().strftime('%y%m%d')
# NOTE: Number of segments is nEchoes * nPhaseSteps
nPoints = int(acq_time*SW_kHz+0.5)
acq_time = nPoints/SW_kHz # ms
logging.debug("ACQUISITION TIME:",acq_time,"ms")
logging.debug("TAU DELAY:",tau_us,"us")
#}}}
# {{{ check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}
prog_p90s = []
for j in range(len(p90_range)):
    prog_p90_us = prog_plen(p90_range[j])
    prog_p180_us = prog_plen(2 * p90_range[j])
    prog_p90s.append(prog_p90_us)
print(prog_p90s)    
nutation_data = run_spin_echo(
        deadtime_us = 20.0,
        nScans=nScans, 
        indirect_idx = 0, 
        indirect_len = len(p90_range), 
        adcOffset = adcOffset,
        carrierFreq_MHz = carrierFreq_MHz, 
        nPoints = nPoints,
        nEchoes=nEchoes, 
        p90_us = p90_range[0], 
        repetition_us = repetition,
        tau_us = tau_us, 
        SW_kHz = SW_kHz, 
        indirect_fields = None, 
        ret_data = None)
nutation_times = nutation_data.getaxis('indirect')
nutation_times[0] = p90_range[0]
for index,p90 in enumerate(p90_range[1:]):
    run_spin_echo(
            nScans=nScans, 
            deadtime_us = 20.0,
            indirect_idx = index+1, 
            indirect_len = len(p90_range), 
            adcOffset = adcOffset,
            carrierFreq_MHz = carrierFreq_MHz, 
            nPoints = nPoints,
            nEchoes=nEchoes, 
            p90_us = p90, 
            repetition_us = repetition,
            tau_us = tau_us, 
            SW_kHz = SW_kHz, 
            ret_data = nutation_data)
    nutation_times[index + 1] = p90
acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_range', 'prog_p90s','deadtime', 'repetition', 'SW_kHz',
    'nPoints', 'deblank_us', 'tau_us', 'nPhaseSteps']}
acq_params['pulprog'] = 'spincore_nutation_v3'
nutation_data.set_prop('acq_params',acq_params)
nutation_data.name('nutation')
myfilename = date + '_' + output_name + '.h5'
nutation_data.chunk('t',['ph1','t2'],[len(ph1_cyc),-1]).setaxis('ph1',ph1_cyc/4)
nutation_data.setaxis('nScans',r_[0:nScans])        
nutation_data.reorder('t2',first=False)
nutation_data.hdf5_write(myfilename)
logging.info("Name of saved data",nutation_data.name())
logging.info("Shape of saved data",ndshape(nutation_data))
SpinCore_pp.stopBoard()
nutation_data.reorder(['ph1','indirect'])
fl.next('raw data')
fl.image(nutation_data.C.setaxis('indirect','#').set_units('indirect','scan #'))
nutation_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(nutation_data.C.setaxis('indirect','#').set_units('indirect','scan #'))
fl.show()

