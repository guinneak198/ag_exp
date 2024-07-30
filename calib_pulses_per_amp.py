r"""
Calibrate pulses output from RF amplifier
=========================================
A series of betas ($\mu$s $\sqrt{W}$) are supplied to the spincore to output to
the RF amplifier. The output of the amplifier is then captured on the GDS
oscilloscope. It is very important to note that there MUST BE at least a 40 dBm
attenuator between the RF amplifier output and the GDS oscilloscope input to
avoid damaging the instrumentation! It is advised that the attenuator be
calibrated using the GDS and AFG beforehand
"""
import pyspecdata as psd
import os
import SpinCore_pp as spc
from datetime import datetime
from Instruments import GDS_scope
import numpy as np

my_exp_type = "test_equipment"
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
# {{{ add file saving parameters to config dict
config_dict["type"] = "pulse_calib"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["misc_counter"] += 1
# }}}
# {{{ ppg
sqrt_P = config_dict["amplitude"] * np.sqrt(75)  # we have a 75 W amplifier
prog_beta = np.linspace(10, 100, 50, endpoint=False)
p90s_range = prog_beta / sqrt_P
tx_phases = np.r_[0.0, 90.0, 180.0, 270.0]
Rx_scans = 1
datalist = []
with GDS_scope() as gds:
    for index, val in enumerate(p90s_range):
        p90 = val
        p180 = 2 * val
        spc.configureTX(
            config_dict["adc_offset"],
            config_dict["carrierFreq_MHz"],
            tx_phases,
            config_dict["amplitude"],
            nPoints,
        )
        acq_time = spc.configureRX(
            config_dict["SW_kHz"], nPoints, Rx_scans, config_dict["nEchoes"], 1
        )  # Not phase cycling so setting nPhaseSteps to 1
        config_dict["acq_time_ms"] = acq_time
        spc.init_ppg()
        spc.load(
            [
                ("phase_reset", 1),
                ("delay_TTL", 1.0),
                ("pulse_TTL", p90, 0),
                ("delay", config_dict["tau_us"]),
                ("delay_TTL", 1.0),
                ("pulse_TTL", p180, 0),
                ("delay", config_dict["deadtime_us"]),
                ("acquire", config_dict["acq_time_ms"]),
            ]
        )
        spc.stop_ppg()
        spc.runBoard()
        datalist.append(gds.waveform(ch=2))
        spc.stopBoard()
data = psd.concat(datalist, "p_90").reorder("t")
data.set_units("t", "s")
data.set_prop("set_p90s", p90s_range)
data.set_prop("set_p180s", 2 * p90s_range)
data.set_prop("set_beta", prog_beta)
data.set_prop("acq_params", config_dict.asdict())
config_dict = spc.save_data(data, my_exp_type, config_dict, "misc")
config_dict.write()
