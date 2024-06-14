from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp import prog_plen
from SpinCore_pp.ppg import generic
import os
from datetime import datetime
import h5py
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["echo_acq_ms"] * config_dict["SW_kHz"] + 0.5)
config_dict["acq_time_ms"] = nPoints / config_dict["SW_kHz"]
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "echo"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_generic_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    
    #ph1_cyc = r_[0,1,2,3]
    #ph2_cyc = r_[0,2]
    #nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    ph_overall = r_[0, 1, 2, 3]
    ph_diff = r_[0, 2]
    ph1_cyc = array([(j + k) % 4 for k in ph_overall for j in ph_diff])
    ph2_cyc = array([(k + 1) % 4 for k in ph_overall for j in ph_diff])
    nPhaseSteps = len(ph_overall) * len(ph_diff)
# }}}
# {{{symmetric tau
prog_p90_us = prog_plen(config_dict['p90_us'])
print(prog_p90_us)
prog_p180_us = prog_plen(2*config_dict['p90_us'])
short_delay_us = 1.0
tau_evol_us = (
    prog_p180_us / pi
)  # evolution during pulse -- see eq 6 of coherence paper
pad_end_us = (
    config_dict["deadtime_us"] - config_dict["deblank_us"] - 2 * short_delay_us
)
twice_tau_echo_us = config_dict["echo_acq_ms"] * 1e3 + (
    2 * config_dict["deadtime_us"]
)  # the period between end of first 180 pulse and start of next
config_dict["tau_us"] = (
    twice_tau_echo_us / 2.0 - tau_evol_us - config_dict["deblank_us"]
)
print("using a tau of:",config_dict['tau_us'])
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps# * config_dict['nEchoes']
#assert total_pts < 2 ** 14, (
#    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the echo_acq_ms to %f"
#    % (total_pts, config_dict["echo_acq_ms"] * 16384 / total_pts)
#)
# }}}
# {{{basic phasecycling
data = generic(
    ppg_list=[
        ("phase_reset", 1),
        ("delay_TTL", config_dict["deblank_us"]),
        #("pulse_TTL", prog_p90_us, "ph1", ph1_cyc),
        ("pulse_TTL", prog_p90_us, "ph_cyc", ph1_cyc),
        ("delay", config_dict["tau_us"]),
        ("delay_TTL", config_dict["deblank_us"]),
        #("pulse_TTL", prog_p180_us, "ph2", r_[0]),
        ("pulse_TTL", prog_p180_us, "ph_cyc", ph2_cyc),
        ("delay", config_dict["deadtime_us"]),
        ("acquire", config_dict["echo_acq_ms"]),
        ("delay",pad_end_us),
        ("delay",short_delay_us),
        ("marker","echo_label", (config_dict['nEchoes']-1)),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", prog_p180_us, "ph_cyc", ph2_cyc),
        ("delay", config_dict["deadtime_us"]),
        ("acquire", config_dict["echo_acq_ms"]),
        ("delay", pad_end_us),
        ("jumpto", "echo_label"),
        ("delay", config_dict["repetition_us"]),
    ],
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=config_dict["nEchoes"],
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    acq_time_ms=config_dict["echo_acq_ms"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
## {{{ chunk and save data
data.set_prop('postproc_type','proc_Hahn_echoph')
#data.chunk(
#    "t", 
    #["ph1", "t2"], 
    #[4,-1])
#    ["ph_overall","ph_diff","t2"],
#    [len(ph_overall),len(ph_diff),-1]).labels({
#        "ph_overall":r_[0:len(ph_overall)],
#        "ph_diff":r_[0:len(ph_diff)]})
#data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
#data.setaxis("nScans", r_[0 : config_dict["nScans"]])
#data.setaxis("ph_overall", ph_overall/4)
#data.setaxis("ph_diff", ph_diff/4)
# }}}
data.name(config_dict["type"] + "_" + str(config_dict["cpmg_counter"]))
data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
filename_out = filename + ".h5"
nodename = data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_cpmg")
            data.name("temp_cpmg")
            nodename = "temp_cpmg"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_cpmg.h5 in the current h5 file"
        )
        if os.path.exists("temp_cpmg.h5"):
            print("there is a temp_cpmg.h5 already! -- I'm removing it")
            os.remove("temp_cpmg.h5")
            data.hdf5_write("temp_cpmg.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_cpmg.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()

