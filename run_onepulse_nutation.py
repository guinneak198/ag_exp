"""
One Pulse Experiment
====================

Not an echo detection but rather just capturing
the FID with a 4-step phase cycle. 
"""

import pyspecdata as psd
from numpy import r_, linspace
import sys
import os
import h5py
import SpinCore_pp
import SpinCore_pp as spc
from SpinCore_pp.ppg import generic
from datetime import datetime
from Instruments.XEPR_eth import xepr

my_exp_type = "ODNP_NMR_comp/nutation"
assert os.path.exists(psd.getDATADIR(exp_type=my_exp_type))
beta_range_s_sqrt_W = linspace(0.1e-6,250e-6,32)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = spc.get_integer_sampling_intervals(
    SW_kHz=config_dict["SW_kHz"],
    time_per_segment_ms=config_dict["acq_time_ms"],
)
# }}}
# {{{add file saving parameters to config dict
config_dict["type"] = "FID_nutation"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["echo_counter"] += 1
# }}}
# {{{ command-line option to leave the field untouched (if you set it once, why set it again)
adjust_field = True
if len(sys.argv) == 2 and sys.argv[1] == "stayput":
    adjust_field = False
# }}}
# {{{ let computer set field
if adjust_field:
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
# }}}
# {{{set phase cycling
ph1_cyc = r_[0, 1, 2, 3]
nPhaseSteps = 4
# }}}
prog_p90_us = spc.prog_plen(beta_range_s_sqrt_W, config_dict["amplitude"])
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
# {{{ acquire FID nutation
data = None
for idx, p90_us in enumerate(prog_p90_us):
    data = generic(
        ppg_list=[
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", p90_us, "ph1", ph1_cyc),
            ("delay", config_dict["deadtime_us"]),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", config_dict["repetition_us"]),
        ],
        nScans=config_dict["nScans"],
        indirect_idx=idx,
        indirect_len=len(beta_range_s_sqrt_W),
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        time_per_segment_ms=config_dict["acq_time_ms"],
        SW_kHz=config_dict["SW_kHz"],
        amplitude=config_dict["amplitude"],
        ret_data=data,
    )
# }}}
data.rename("indirect", "beta")
data.setaxis("beta", beta_range_s_sqrt_W).set_units("beta", "s√W")
data.set_prop("p_90s", prog_p90_us)
# {{{ In a repo where the nutation counter doesn't exist so I do it manually here
# {{{ chunk and save data
data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
data.setaxis("ph1", ph1_cyc / 4)
if config_dict["nScans"] > 1:
    data.setaxis("nScans", r_[0 : config_dict["nScans"]])
data.reorder(["nScans", "ph1", "beta", "t2"])
data.set_units("t2", "s")
data.set_prop("postproc_type", "spincore_FID_nutation_v1")
data.set_prop("coherence_pathway", {"ph1": -1})
data.set_prop("acq_params", config_dict.asdict())
target_directory = psd.getDATADIR(exp_type = my_exp_type)
filename_out = f"{config_dict['date']}_{config_dict['chemical']}_FID_nutation"+".h5"
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
