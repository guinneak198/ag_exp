# Just capturing FID, not echo detection
# 4-step phase cycle
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp import prog_plen
from SpinCore_pp.ppg import generic
import os
from datetime import datetime
import h5py
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
from Instruments import power_control
phase_cycling = True
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
target_directory = getDATADIR(exp_type = 'ODNP_NMR_comp/Echoes')
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "FID"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_generic_{config_dict['type']}"
# }}}
#{{{let computer set field
print("I'm assuming that you've tuned your probe to",
        config_dict['carrierFreq_MHz'],
        "since that's what's in your .ini file",
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
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#}}}
prog_p90_us = prog_plen(config_dict['p90_us'])
# {{{check total points
total_pts = nPoints * nPhaseSteps# * config_dict['nEchoes']
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
# }}}
data = generic(
    ppg_list = [
        ('marker','start',1),
        ('phase_reset',1),
        ('delay_TTL',config_dict['deblank_us']),
        ('pulse_TTL',prog_p90_us,'ph1',ph1_cyc),
        ('delay',config_dict['deadtime_us']),
        ('acquire',config_dict['acq_time_ms']),
        ('delay',config_dict['repetition_us']),
        ('jumpto','start')
        ],
    nScans = config_dict['nScans'],
    indirect_idx = 0,
    indirect_len = 1,
    adcOffset = config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    time_per_segment_ms=config_dict["acq_time_ms"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
data.set_prop('postproc_type','spincore_FID_v1')
data.set_prop("acq_params", config_dict.asdict())
data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
data.chunk(
    "t", 
    ["ph1", "t2"], 
    [4,-1])
data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
# }}}
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/FID")
filename_out = filename + ".h5"
nodename = data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_cpmg")
            data.name("temp_FID")
            nodename = "temp_FID"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_FID.h5 in the current h5 file"
        )
        if os.path.exists("temp_FID.h5"):
            print("there is a temp_FID.h5 already! -- I'm removing it")
            os.remove("temp_FID.h5")
            data.hdf5_write("temp_FID.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_FID.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()

