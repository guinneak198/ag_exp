"""
SpinCore Noise Acquisition
==========================

This is a copy of capture_noise_SC, where the
SW, aq length, and nScans are hard-coded,
since they are very different from typical
values, and we do *not* want to enter them
into active.ini
"""
import pyspecdata as ps
import numpy as np
import os
from numpy import r_
import SpinCore_pp as sc
from datetime import datetime
import time

my_exp_type = "ODNP_NMR_comp/noise_tests"
nScans = 100

sc.adc_offset()


# {{{ Function for data acquisition
def collect(config_dict):
    """
    Collects `nScans` identical captures (specified by the config file) of the
    noise as acquired on the SpinCore.
    The resulting data has a direct dimension called `t` and the
    acquisitions are repeated along the `nScans` dimension.
    :Note: Some delays (e.g. the repetition
    and time between phase reset and acquisition
    are hard set to short values and are not pulled or stored in the
    config file).

    Parameters
    ==========
    config_dict: dict-like
        Contains the following keys:

        :SW_kHz: float
        :nScans: int
        :adc_offset: float
        :amplitude: float
        :carrier frequency: float
        :acq_time_ms: float
        :chemical: str
        :type: str
        :noise_counter: int

    Returns
    =======
    data: nddata
        nddata containing captures of noise as acquired on the SpinCore.
    """
    # {{{ SpinCore settings - these don't change
    tx_phases = r_[0.0, 90.0, 180.0, 270.0]
    (
        nPoints,
        SW_kHz, # 200 kHz
        time_per_segment_ms, # 10 ms
    ) = sc.get_integer_sampling_intervals(
        SW_kHz=200.0,
        time_per_segment_ms=10.0,
    )
    RX_nScans = 1
    # }}}
    # {{{ Acquire data
    for j in range(nScans):
        # {{{ configure SpinCore
        sc.configureTX(
            config_dict["adc_offset"],
            config_dict["carrierFreq_MHz"],
            tx_phases,
            config_dict["amplitude"],
            nPoints,
        )
        acq_time_ms = sc.configureRX(
            SW_kHz,
            nPoints,
            RX_nScans,
            1,  # assume nEchoes = 1
            1,  # assume nPhaseSteps = 1
        )
        sc.init_ppg()
        # }}}
        # {{{ ppg to generate the SpinCore data
        sc.load(
            [
                ("marker", "start", 1),
                ("phase_reset", 1),
                ("delay", 0.5e3),  # pick short delay (0.5 ms)
                ("acquire", acq_time_ms),
                ("delay", 1e4),  # short rep_delay_us (10 ms)
                ("jumpto", "start"),
            ]
        )
        # }}}
        sc.stop_ppg()
        sc.runBoard()
        # {{{grab data for the single capture as a complex value
        #    - raw data variable needed here to dictate size of time axis
        raw_data = (
            sc.getData((2 * nPoints * 1 * 1), nPoints, 1, 1)
            .astype(float)
            .view(complex)
        )  # assume nEchoes and nPhaseSteps = 1
        # }}}
        # {{{ if this is the first scan, then allocate an array
        #     to drop the data into, and assign the axis
        #     coordinates, etc.
        if j == 0:
            time_axis = np.linspace(0.0, acq_time_ms * 1e-3, raw_data.size)
            data = (
                ps.ndshape(
                    [raw_data.size, nScans],
                    ["t", "nScans"],
                )
                .alloc(dtype=np.complex128)
                .setaxis("t", time_axis)
                .set_units("t", "s")
                .setaxis("nScans", np.zeros(nScans))
                .name("noise_capture")
            )
        # }}}
        data["nScans", j] = raw_data
        data["nScans"][j] = time.time()
        # }}}
        sc.stopBoard()
    # }}}
    return data


# }}}
# {{{ set up config file and define exp_type
assert os.path.exists(ps.getDATADIR(exp_type=my_exp_type))
config_dict = sc.configuration("active.ini")
# since this is typically the first time interacting with the SC board, go
# ahead and run adc offset
config_dict["adc_offset"] = sc.adc_offset()
# {{{ add file saving parameters to config dict
config_dict["type"] = "noise_200kHz"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["noise_counter"] += 1
# }}}
# }}}
print("Starting collection...")
data = collect(config_dict)
print("Collection time:", np.diff(data["nScans"][r_[0, -1]]), "s")
data.set_prop("postproc_type", "spincore_general")
data.set_prop("acq_params", config_dict.asdict())
data.set_units("t", "s")
config_dict = sc.save_data(data, my_exp_type, config_dict, "noise")
config_dict.write()
