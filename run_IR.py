'''Run Inversion Recovery at set power
======================================
You will need to manually set the power manually with Spyder and the B12. Once the power is set and the parameters are adjusted, you can run this program to collect the inversion recovery dataset at the set power.
'''
import numpy as np
from numpy import r_
from pyspecdata import *
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from pyspecdata import strm
import os, sys, time
import h5py
import SpinCore_pp
from SpinCore_pp.power_helper import Ep_spacing_from_phalf
from SpinCore_pp.ppg import run_spin_echo, run_IR
from Instruments import power_control
from datetime import datetime
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'IR'
config_dict['date'] = date
config_dict['IR_counter'] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
filename_out = filename +'.h5'
#{{{phase cycling
IR_ph1_cyc = r_[0, 2]
IR_ph2_cyc = r_[0, 2]
total_pts = nPoints*len(IR_ph2_cyc)*len(IR_ph1_cyc)
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{make vd list
vd_kwargs = {
        j:config_dict[j]
        for j in ['krho_cold','krho_hot','T1water_cold','T1water_hot']
        if j in config_dict.keys()
        }
#vd_list_us = SpinCore_pp.vdlist_from_relaxivities(config_dict['concentration'],**vd_kwargs) * 1e6 #put vd list into microseconds
vd_list_us = np.linspace(5e1,3.2e6,8)
#}}}
#{{{run IR
vd_data = None
for vd_idx,vd in enumerate(vd_list_us):
    vd_data = run_IR(
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            indirect_idx=vd_idx,
            indirect_len=len(vd_list_us),
            ph1_cyc=IR_ph1_cyc,
            ph2_cyc=IR_ph2_cyc,
            vd=vd,
            nScans=config_dict["nScans"],
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            p90_us=config_dict["p90_us"],
            tau_us=config_dict["tau_us"],
            repetition_us=6.0,
            SW_kHz=config_dict["SW_kHz"],
            ret_data=vd_data,
        )
vd_data.rename("indirect", "vd")
vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
vd_data.set_prop("acq_params", config_dict.asdict())
vd_data.set_prop("postproc_type", "spincore_IR_v1")
vd_data.name('FIR')
vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph2_cyc), len(IR_ph1_cyc), -1])
vd_data.setaxis("ph1", IR_ph1_cyc / 4)
vd_data.setaxis("ph2", IR_ph2_cyc / 4)
vd_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
nodename = vd_data.name()
with h5py.File(
    os.path.normpath(os.path.join(target_directory,f"{filename_out}")
)) as fp:
    if nodename in fp.keys():
        print("this nodename already exists, so I will call it temp_%d"%j)
        vd_data.name("temp_%d"%j)
        nodename = "temp_%d"%j
        vd_data.hdf5_write(f"{filename_out}",directory = target_directory)
    else:
            vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",vd_data.name()))
print(("Shape of saved data",ndshape(vd_data)))
config_dict.write()
#}}}
#{{{visualize raw data
vd_data.ift('t2')
fl.next('raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('abs raw data')
fl.image(abs(vd_data).setaxis('vd','#'))
vd_data.ft('t2')
fl.next('FT raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('FT abs raw data')
fl.image(abs(vd_data).setaxis('vd','#')['t2':(-1e3,1e3)])
fl.show()
#}}}
