r"""
Use the Scope to Calibrate pulses output from RF amplifier
===========================================================
If calibrating the pulse lengths, a series of pulse lengths are sent to the 
spincore directly and the output pulse is captured on the GDS oscilloscope.
If testing the calibration or capturing using a series of desired betas,
the calibrating conditional should be set to false and the script will calibrate
the pulse lengths so that the output of the amplifier produces the desired beta.
It is very important to note that there MUST BE at least a 40 dBm
attenuator between the RF amplifier output and the GDS oscilloscope input to
avoid damaging the instrumentation! It is advised that the attenuator be
calibrated using the GDS and AFG beforehand
"""
import pyspecdata as psd
import os
import time
import SpinCore_pp as spc
from datetime import datetime
from Instruments import GDS_scope
from numpy import r_
import numpy as np

calibrating = True

indirect = "t_pulse" if calibrating else "beta"
my_exp_type = "test_equipment"
nominal_power = 75
nominal_atten = 1e4
num_div_per_screen = 8
n_lengths = 50
assert os.path.exists(psd.getDATADIR(exp_type=my_exp_type))
# {{{ importing acquisition parameters
config_dict = spc.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = spc.get_integer_sampling_intervals(
    config_dict["SW_kHz"], config_dict["acq_time_ms"]
)
# }}}
if calibrating:
    t_pulse_us = np.linspace(
        # if the amplitude is small we want to go out to much longer pulse lengths
        0.5 / np.sqrt(nominal_power) / config_dict["amplitude"],
        350 / np.sqrt(nominal_power) / config_dict["amplitude"],
        n_lengths,
    )
else:
    desired_beta = np.linspace(0.5e-6, 400e-6, n_lengths)  # s *sqrt(W)
    t_pulse_us = spc.prog_plen(desired_beta, config_dict["amplitude"])
# {{{ add file saving parameters to config dict
config_dict["type"] = "pulse_calib"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["misc_counter"] += 1
# }}}
# {{{ ppg
tx_phases = np.r_[0.0, 90.0, 180.0, 270.0]
with GDS_scope() as gds:
    # {{{ set up settings for GDS
    gds.reset()
    gds.CH1.disp = True
    gds.CH2.disp = True
    gds.write(":CHAN1:DISP OFF")
    gds.write(":CHAN2:DISP ON")
    gds.write(":CHAN3:DISP OFF")
    gds.write(":CHAN4:DISP OFF")
    gds.write(":CHAN2:IMP 5.0E+1")  # set impedance to 50 ohm
    gds.write(":TRIG:SOUR CH2")
    gds.write(":TRIG:MOD NORMAL")  # set trigger mode to normal
    gds.write(":TRIG:LEV 34E-3")  # set trigger level

    def round_for_scope(val, multiples=1):
        val_oom = np.floor(np.log10(val))
        val = (
            np.ceil(val / 10**val_oom / multiples)
            * 10**val_oom
            * multiples
        )
        return val

    gds.CH2.voltscal = round_for_scope(
        config_dict["amplitude"]
        * np.sqrt(2 * nominal_power / nominal_atten * 50)
        * 2
        / num_div_per_screen
    )  # 2 inside is for rms-amp 2 outside is for positive and negative
    print("here is the max pulse length", t_pulse_us.max())
    scope_timescale = round_for_scope(
        t_pulse_us.max() * 1e-6 * 0.5 / num_div_per_screen, multiples=5
    )
    print(
        "here is the timescale in μs", scope_timescale / 1e-6
    )  # the 0.5 is because it can fit in half the screen
    gds.timscal(
        scope_timescale,
        pos=round_for_scope(0.5 * t_pulse_us.max() * 1e-6 - 3e-6),
    )
    # }}}
    data = None
    for idx, this_t_pulse in enumerate(t_pulse_us):
        spc.configureTX(
            config_dict["adc_offset"],
            config_dict["carrierFreq_MHz"],
            tx_phases,
            config_dict["amplitude"],
            nPoints,
        )
        acq_time_ms = spc.configureRX(
            # Rx scans, echos, and nPhaseSteps set to 1
            config_dict["SW_kHz"],
            nPoints,
            1,
            1,
            1,
        )
        config_dict["acq_time_ms"] = acq_time_ms
        spc.init_ppg()
        spc.load(
            [
                ("phase_reset", 1),
                ("delay_TTL", 1.0),
                ("pulse_TTL", this_t_pulse, 0),
                ("delay", config_dict["deadtime_us"]),
            ]
        )
        spc.stop_ppg()
        spc.runBoard()
        spc.stopBoard()
        time.sleep(1.0)
        thiscapture = gds.waveform(ch=2)
        assert (
            np.diff(thiscapture["t"][r_[0:2]]).item() < 0.5 / 24e6
        ), "what are you trying to do, you dwell time is too long!!!"
        # {{{ just convert to analytic here, and also downsample
        #     this is a rare case where we care more about not keeping
        #     ridiculous quantities of garbage on disk, so we are going
        #     to throw some stuff out beforehand
        thiscapture.ft("t", shift=True)
        thiscapture = thiscapture["t":(0, None)]["t":(None, 24e6)]
        thiscapture *= 2
        thiscapture["t", 0] *= 0.5
        thiscapture.ift("t")
        # }}}
        if data is None:
            data = thiscapture.shape
            data += (indirect, n_lengths)
            data = data.alloc()
            data.copy_axes(thiscapture)
            data.copy_props(thiscapture)
        data[indirect, idx] = thiscapture
if calibrating:
    data.setaxis(
        "t_pulse", t_pulse_us * 1e-6
    )  # always store in SI units unless we're wanting to change the variable name
    data.set_units("t_pulse", "s")
else:
    data.setaxis("beta", desired_beta)
    data.set_prop("programmed_t_pulse_us", t_pulse_us * 1e-6)
data.set_prop("postproc_type", "GDS_capture_v1")
data.set_units("t", "s")
data.set_prop("acq_params", config_dict.asdict())
config_dict = spc.save_data(data, my_exp_type, config_dict, "misc", proc=False)
config_dict.write()
