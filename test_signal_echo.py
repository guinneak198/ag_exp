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
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import SpinCore_pp
import h5py
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
from Instruments import power_control
fl = figlist_var()
#{{{importing acquisition parameters
SW_kHz = 3.9
filename = '240214_test_signal_echo1_'+str(SW_kHz) +'kHz'
adcOffset = 45
carrierFreq_MHz = 14.9
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
p90 = 4.0
deadtime = 10.0
repetition = 1e4
nPoints = 1024*2

acq_time = 1024#nPoints/SW_kHz + 1.0 # ms
tau_adjust = 0.0
deblank = 1.0
tau = 3500#deadtime + acq_time*1e3*(1./8.) + tau_adjust
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
#}}}


#{{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{check total points
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{acquire echo
echo_data = run_spin_echo(
        nScans=1,
        indirect_idx = 0,
        indirect_len = 1,
        ph1_cyc = ph1_cyc,
        adcOffset = adcOffset,
        carrierFreq_MHz = carrierFreq_MHz,
        nPoints = nPoints,
        nEchoes = 1,
        p90_us = p90,
        repetition_us = repetition,
        tau_us = tau,
        SW_kHz = SW_kHz,
        ret_data = None)
#}}}
#{{{setting acq_params
echo_data.set_prop("postproc_type","proc_Hahn_echoph")
echo_data.name('signal')
#}}}
#{{{Look at raw data
if phase_cycling:
    echo_data.chunk('t',['ph1','t2'],[4,-1])
    echo_data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    echo_data.setaxis('nScans',r_[0:1])
    echo_data.reorder(['ph1','nScans','t2'])
    fl.next('image')
    fl.image(echo_data.C.mean('nScans'))
    echo_data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(echo_data.C.mean('nScans'))
    fl.next('image - ft, coherence')
    echo_data.ft(['ph1'])
    fl.image(echo_data.C.mean('nScans'))
    fl.next('data plot')
    data_slice = echo_data['ph1',1].C.mean('nScans')
    fl.plot(data_slice, alpha=0.5)
    fl.plot(data_slice.imag, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
else:
    fl.next('raw data')
    fl.plot(echo_data)
    echo_data.ft('t',shift=True)
    fl.next('ft')
    fl.plot(echo_data.real)
    fl.plot(echo_data.imag)
    fl.plot(abs(echo_data),color='k',alpha=0.5)
#}}}    
filename_out = filename + '.h5'
nodename = echo_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            echo_data.name("temp")
            nodename = "temp"
    echo_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        echo_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            echo_data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )

print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
fl.show()
