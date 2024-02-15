"""
Varied Tau Experiment
=====================

A standard echo that is repeated varying the echo time between pulses. The tau value is adjusted 
to ensure a symmetric echo.
"""
from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import socket
import sys
import time
import h5py

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "Var_Tau"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['echo_counter']}"
# }}}
#{{{Parameters that change for new samples
nEchoes = 1
ph1_cyc = r_[0,1,2,3]
SW_kHz =  3.9 #originally
acq_time = 1024
nPhaseSteps = 4
#}}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
nPoints = int(acq_time*SW_kHz+0.5)

tau = list(linspace(7e3,37e3,8,endpoint=False))
#tau.reverse()
print("YOUR TAUS ARE:")
print(tau)
input("Does this look right?")
tau_axis = tau
# }}}
# {{{check total points

#total_pts = nPoints * nPhaseSteps
#assert total_pts < 2 ** 14, (
#    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
#    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
#)
# }}}
# {{{ check for file
myfilename = filename + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}
# {{{ acquire varied tau data
var_tau_data = run_spin_echo(
        nScans=config_dict['nScans'], 
        indirect_idx = 0, 
        indirect_len = int(len(tau)), 
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'], 
        nPoints = nPoints,
        nEchoes=1, 
        p90_us = config_dict['p90_us'], 
        repetition_us = config_dict['repetition_us'],
        tau_us = tau_axis[0], 
        SW_kHz = SW_kHz, 
        ph1_cyc = ph1_cyc, 
        ret_data = None)
mytau_axis = var_tau_data.getaxis("indirect")
mytau_axis[0] = tau_axis[0]
# {{{run varied tau
for tau_idx, val in enumerate(tau_axis[1:]):
    tau = val  # us
    var_tau_data = run_spin_echo(
        nScans=config_dict['nScans'], 
        indirect_idx = tau_idx+1, 
        indirect_len = int(len(tau_axis)), 
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'], 
        nPoints = nPoints,
        nEchoes=1, 
        p90_us = config_dict['p90_us'], 
        repetition_us = config_dict['repetition_us'],
        tau_us = tau, 
        SW_kHz = SW_kHz, 
        ph1_cyc = ph1_cyc, 
        ret_data = var_tau_data)
    mytau_axis[tau_idx+1] = tau
var_tau_data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
var_tau_data.set_prop("postproc_type","SpinCore_var_tau_v1") #still needs to be added to load_Data
var_tau_data.set_prop("acq_params", config_dict.asdict())
filename_out = filename + ".h5"
nodename = var_tau_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_var_tau")
            var_tau_data.name("temp_var_tau")
            nodename = "temp_var_tau"
        var_tau_data.hdf5_write(f"{filename_out}")
else:
    try:
        var_tau_data.hdf5_write(f"{filename_out}")
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_var_tau.h5 in the current directory"
        )
        if os.path.exists("temp_var_tau.h5"):
            print("there is a temp_var_tau.h5 already! -- I'm removing it")
            os.remove("temp_var_tau.h5")
            var_tau_data.hdf5_write("temp_var_tau.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_var_tau.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", var_tau_data.name()))
config_dict.write()
fl.show()
