"""
Nutation
========

A standard echo where the 90 time is varied so 
that we are able to see when the signal rotates through 90 to 
180 degrees.
"""
import pyspecdata as psd
import sys
import os
import SpinCore_pp
from SpinCore_pp import get_integer_sampling_intervals, save_data
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import numpy as np
from numpy import r_

my_exp_type = "ODNP_NMR_comp/nutation"
assert os.path.exists(psd.getDATADIR(exp_type=my_exp_type))
beta_range = np.linspace(0.1e-6, 300e-6, 32)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = get_integer_sampling_intervals(
    config_dict["SW_kHz"], config_dict["acq_time_ms"]
)
# }}}
# {{{add file saving parameters to config dict
config_dict["type"] = "nutation"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["echo_counter"] += 1
# }}}
# {{{set phase cycling
ph1_cyc = r_[0, 2]
ph2_cyc = r_[0, 2]
nPhaseSteps = len(ph1_cyc) * len(ph2_cyc)
# }}}
# {{{ command-line option to leave the field untouched (if you set it once, why set it again)
adjust_field = True
if len(sys.argv) == 2 and sys.argv[1] == "stayput":
    adjust_field = False
# }}}
input(
    "I'm assuming that you've tuned your probe to %f since that's what's in your .ini file. Hit enter if this is true"
    % config_dict["carrierFreq_MHz"]
)
# {{{ let computer set field
if adjust_field:
    spc.set_field(config_dict)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
data = None
for idx, beta_s_sqrtW in enumerate(beta_range):
    # Just loop over the 90 times and set the indirect axis at the end
    # just like how we perform and save IR data
    data = run_spin_echo(
        deadtime_us=config_dict["deadtime_us"],
        nScans=config_dict["nScans"],
        indirect_idx=idx,
        indirect_len=len(beta_range),
        ph1_cyc=ph1_cyc,
        ph2_cyc = ph2_cyc,
        amplitude=config_dict["amplitude"],
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        beta_90_s_sqrtW=beta_s_sqrtW,
        repetition_us=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        ret_data=data,
    )
if 'indirect' in data.dimlabels:
    data.rename("indirect","beta")
data.setaxis("beta", beta_range).set_units("beta", "s√W")
# {{{ chunk and save data
data.chunk("t", ["ph2", "ph1", "t2"], [2, 2, -1])
data.setaxis("ph1", ph1_cyc / 4).setaxis("ph2", ph2_cyc / 4)
if config_dict["nScans"] > 1:
    data.setaxis("nScans", r_[0 : config_dict["nScans"]])
data.reorder(["ph2", "ph1", "nScans", "t2"])
data.set_units("t2", "s")
data.set_prop("postproc_type", "spincore_FID_nutation_v1")
data.set_prop("coherence_pathway", {"ph1": +1, "ph2":-2})
data.set_prop("acq_params", config_dict.asdict())
target_directory = psd.getDATADIR(exp_type = my_exp_type)
filename_out = f"{config_dict['date']}_{config_dict['chemical']}_nutation"+".h5"
nodename = config_dict["type"] + "_" + str(config_dict["echo_counter"])
data.name(nodename)
if os.path.exists(f"{target_directory}{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        while nodename in fp.keys():
            config_dict["echo_counter"] += 1
            nodename = (
                config_dict["type"]
                + "_"
                + str(config_dict["echo_counter"])
            )
        data.name(nodename)
data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n** FILE SAVED IN TARGET DIRECTORY ***\n")
print(
    "saved data to (node, file, exp_type):",
    data.name(),
    filename_out,
    my_exp_type,
)
config_dict.write()
# }}}
