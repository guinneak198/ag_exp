from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
from SpinCore_pp.ppg import run_spin_echo
import logging
fl = figlist_var()
#{{{Parameters that change for new samples
output_name = 'ras_batch2310_L118_a_nutation_1'
adcOffset = 50
carrierFreq_MHz = 14.886083
nScans = 1
nEchoes = 1
repetition = 10.0e6
p90_range = linspace(7,14,5,endpoint=False)
ph1_cyc = r_[0,1,2,3]
SW_kHz = 3.9 #24.0 originally
acq_time = 1024
tau = 3500
#}}}
#{{{These should stay the same regardless of sample
date = datetime.now().strftime('%y%m%d')
# NOTE: Number of segments is nEchoes * nPhaseSteps
nPoints = int(acq_time*SW_kHz+0.5)
acq_time = nPoints/SW_kHz # ms
logging.debug("ACQUISITION TIME:",acq_time,"ms")
logging.debug("TAU DELAY:",tau,"us")
#}}}
# {{{ check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}

nutation_data = run_spin_echo(
        nScans=nScans, 
        indirect_idx = 0, 
        indirect_len = len(p90_range), 
        adcOffset = adcOffset,
        carrierFreq_MHz = carrierFreq_MHz, 
        nPoints = nPoints,
        nEchoes=nEchoes, 
        p90_us = p90_range[0], 
        repetition_us = repetition,
        tau_us = tau, 
        SW_kHz = SW_kHz, 
        indirect_fields = None, 
        ph1_cyc = ph1_cyc, 
        ret_data = None)
nutation_times = nutation_data.getaxis('indirect')
nutation_times[0] = p90_range[0]
for index,p90 in enumerate(p90_range[1:]):
    run_spin_echo(
            nScans=nScans, 
            indirect_idx = index+1, 
            indirect_len = len(p90_range), 
            adcOffset = adcOffset,
            carrierFreq_MHz = carrierFreq_MHz, 
            nPoints = nPoints,
            nEchoes=nEchoes, 
            p90_us = p90, 
            repetition_us = repetition,
            tau_us = tau, 
            SW_kHz = SW_kHz, 
            ph1_cyc = ph1_cyc, 
            ret_data = nutation_data)
    nutation_times[index + 1] = p90
acq_params = {j:eval(j) for j in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_range', 'deadtime', 'repetition', 'SW_kHz',
    'nPoints', 'deblank_us', 'tau', 'nPhaseSteps']}
acq_params['pulprog'] = 'spincore_nutation_v3'
nutation_data.set_prop('acq_params',acq_params)
nutation_data.name('nutation')
myfilename = date + '_' + output_name + '.h5'
nutation_data.chunk('t',
        ['ph1','t2'],[len(ph1_cyc),-1]).setaxis(
                'ph1',ph1_cyc/4)
nutation_data.reorder('t2',first=False)
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/nutation")
if os.path.exists(myfilename):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, myfilename))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            nutation_data.name("temp")
            nodename = "temp"
    nutation_data.hdf5_write(myfilename, directory=target_directory)
else:
    try:
        nutation_data.hdf5_write(myfilename, directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {myfilename}, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            nutation_data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", nutation_data.name()))
print(("Shape of saved data", ndshape(nutation_data)))
SpinCore_pp.stopBoard()
nutation_data.reorder(['ph1','indirect'])
fl.next('raw data')
fl.image(nutation_data.C.setaxis('indirect','#').set_units('indirect','scan #'))
nutation_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(nutation_data.C.setaxis('indirect','#').set_units('indirect','scan #'))
fl.show()

