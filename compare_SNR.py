from pylab import *
from pyspecdata import *
# {{{ load the files that we're interested in as different nddata objects
all_data = {}
all_data["reference data 1"] = find_file(
    "230310_test_choke_3p9_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_1",
)
all_data["today"] = find_file(
    "231031_CPMG_prep_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_15",
)
#all_data["today"] = find_file(
#    "231031_CPMG_prep_echo.h5",
#    exp_type="ODNP_NMR_comp/Echoes",
#    expno="echo_14",
#)
all_data["10/12 reference"] = find_file(
    "231012_CPMG_prep_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_12")
show_raw = "today"
noise_starttime = 0.08 # take an std after this point to get the noise
for j in all_data.values():
    j.ift(
        "t2"
    )  # even though it's very sketchy which ppg wrote it, this data was apparently ft'd along all dimensions
# }}}
with figlist_var() as fl:
    obs(
        f"spectral width {all_data[show_raw].get_prop('acq_params')['SW_kHz']}~kHz"
    )
    fl.next(f"raw data for {show_raw}")
    fl.image(all_data[show_raw])
    fl.next("show time domain abs", legend=True)
    for thislabel, thisd in all_data.items():
        forplot = abs(thisd["ph1", 1])["t2":(None, 150e-3)]
        fl.plot(
            forplot,
            label=thislabel
            + "\n%0.4f" % thisd.get_prop("acq_params")["carrierFreq_MHz"]
            + "\n"
            + "noise= %0.2e" % thisd['ph1', 1]['t2':(noise_starttime,None)].run(std,'t2').item()
        )
    fl.next("show time domain abs, normalized", legend=True)
    for thislabel, thisd in all_data.items():
        forplot = abs(thisd["ph1", 1])["t2":(None, 150e-3)]
        fl.plot(forplot / forplot.max(), label=thislabel)
