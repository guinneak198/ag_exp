"""
Field Sweep at constant power
=================================

A ppg that performs a series of echoes at a range of designated field 
values that are determined from the guessed_MHz_to_GHz value in your 
active.ini and the field width parameter. To run this in sync with 
the power_control_server, open a separate terminal on the NMR computer
in your user directory and running "FLInst server" and waiting for it to print
"I am listening..."
"""
import pyspecdata as psd
from pyspecdata import strm
import time
import logging
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import numpy as np
from numpy import r_
from Instruments import power_control
from Instruments.XEPR_eth import xepr

fl = psd.figlist_var()
mw_freqs = []
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{make field axis
left = (
    config_dict["guessed_mhz_to_ghz"] * config_dict["uw_dip_center_GHz"]
) / config_dict["gamma_eff_MHz_G"]
left = left - (config_dict["field_width"] / 2)
right = (
    config_dict["guessed_mhz_to_ghz"] * config_dict["uw_dip_center_GHz"]
) / config_dict["gamma_eff_MHz_G"]
right = right + (config_dict["field_width"] / 2)
assert right < 3700, "Are you crazy??? Field is too high!!!"
assert left > 3300, "Are you crazy??? Field is too low!!!"
print("I see",config_dict['indirect_pts'],"indirect points setting")
field_axis = np.linspace(left,right,config_dict['indirect_pts'])
myinput = input(
    strm("Your field axis is:", field_axis, "\nDoes this look okay?")
)
if myinput.lower().startswith("n"):
    raise ValueError("You said no!!!")
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "field"
config_dict["date"] = date
config_dict["field_counter"] += 1
filename = (
    f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
)
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 1, 2, 3]
    nPhaseSteps = 4
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{ Parameters for Bridge12
powers = r_[config_dict["max_power"]]
min_dBm_step = 0.5
for x in range(len(powers)):
    dB_settings = (
        round(10 * (np.log10(powers[x]) + 3.0) / min_dBm_step) * min_dBm_step
    )  # round to nearest min_dBm_step
print("dB_settings", dB_settings)
print("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW"
    "    or acq time so nPoints x nPhaseSteps is less than 16384\nyou could"
    " try    reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{Run field sweep
with power_control() as p:
    p.set_power(10)
    p.set_freq(config_dict["uw_dip_center_GHz"] * 1e9)
    p.set_power(dB_settings)
    for k in range(10):
        time.sleep(0.5)
        if p.get_power_setting() >= dB_settings:
            break
    if p.get_power_setting() < dB_settings:
        raise ValueError("After 10 tries, this power has still not settled")
    meter_powers = np.zeros_like(dB_settings)
    with xepr() as x_server:
        first_B0 = x_server.set_field(field_axis[0])
        time.sleep(3.0)
        carrierFreq_MHz = config_dict["gamma_eff_MHz_G"] * first_B0
        sweep_data = run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=0,
            indirect_len=len(field_axis),
            ph1_cyc=ph1_cyc,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=carrierFreq_MHz,
            deblank_us=config_dict["deblank_us"],
            plen=config_dict["beta_90_s_sqrtW"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            repetition_us=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            amplitude=config_dict["amplitude"],
            indirect_fields=("Field", "carrierFreq"),
            ret_data=None,
        )
        myfreqs_fields = sweep_data.getaxis("indirect")
        myfreqs_fields[0]["Field"] = first_B0
        myfreqs_fields[0]["carrierFreq"] = carrierFreq_MHz
        for B0_index, desired_B0 in enumerate(field_axis[1:]):
            true_B0 = x_server.set_field(desired_B0)
            logging.info("My field in G is %f" % true_B0)
            time.sleep(3.0)
            new_carrierFreq_MHz = config_dict["gamma_eff_MHz_G"] * true_B0
            myfreqs_fields[B0_index + 1]["Field"] = true_B0
            myfreqs_fields[B0_index + 1]["carrierFreq"] = new_carrierFreq_MHz
            logging.info(strm("My frequency in MHz is", new_carrierFreq_MHz))
            run_spin_echo(
                nScans=config_dict["nScans"],
                indirect_idx=B0_index + 1,
                indirect_len=len(field_axis),
                ph1_cyc=ph1_cyc,
                adcOffset=config_dict["adc_offset"],
                carrierFreq_MHz=new_carrierFreq_MHz,
                nPoints=nPoints,
                deblank_us=config_dict["deblank_us"],
                plen=config_dict["beta_90_s_sqrtW"],
                nEchoes=config_dict["nEchoes"],
                repetition_us=config_dict["repetition_us"],
                tau_us=config_dict["tau_us"],
                SW_kHz=config_dict["SW_kHz"],
                amplitude=config_dict["amplitude"],
                ret_data=sweep_data,
            )
sweep_data.set_prop("acq_params", config_dict.asdict())
# }}}
# {{{chunk and save data
sweep_data.chunk("t", ["ph1", "t2"], [4, -1])
sweep_data.setaxis("ph1", r_[0.0, 1.0, 2.0, 3.0] / 4)
sweep_data.setaxis("nScans", "#")
sweep_data.reorder(["ph1"]).reorder(["nScans"]).reorder(["t2"], first=False)
sweep_data.squeeze()
sweep_data.set_units("t2", "s")

sweep_data.name(config_dict["type"] + "_" + str(config_dict["field_counter"]))
# 8/21/24: JF changed this to v4 b/c there were already files saved with v3 in
# a different format
sweep_data.set_prop("postproc_type", "field_sweep_v4")
sweep_data.set_prop("coherence_pathway", {"ph1": 1})
sweep_data.set_prop("acq_params", config_dict.asdict())
target_directory = "ODNP_NMR_comp/field_dependent"
saving_field = SpinCore_pp.save_data(
    sweep_data, target_directory, config_dict, "field"
)
config_dict.write()
# }}}
fl.show()
