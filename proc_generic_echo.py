from pylab import *
from pyspecdata import *
from pyspecProcScripts.simple_functions import select_pathway
# {{{ load the files that we're interested in as different nddata objects
all_data = {}
pathways = {}
all_data["reference data 1"] = find_file(
    "230310_test_choke_3p9_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_1",
)
pathways["reference data 1"] = {"ph1":1}
all_data["today"] = find_file(
    "231030_CPMG_prep_echo.h5",
    exp_type="ODNP_NMR_comp/Echoes",
    expno="echo_3",
)
pathways["today"] = {"ph1":1}
for j in all_data.values():
    j.ift(
        "t2"
    )  # even though it's very sketchy which ppg wrote it, this data was apparently ft'd along all dimensions
all_data["generic echo"] = find_file(
    "231030_CPMG_test_acq_generic_echo.h5",
    exp_type="ODNP_NMR_comp/CPMG",
    expno="generic_echo_7",
)
all_data["generic echo"].reorder("t2", first=False).ft(['ph_diff','ph_overall'], unitary=True)
pathways["generic echo"] = {"ph_diff":1,# fourier conjugate of ?p1
        "ph_overall":-1,# fourier conjugate of ?p1+?p2
        }
all_data["3 echo cpmg"] = find_file(
    "231030_CPMG_test_acq_CPMG.h5",
    exp_type="ODNP_NMR_comp/CPMG",
    expno="CPMG_15",
)
all_data['3 echo cpmg'].chunk("t", ["ph_overall","ph_diff","t2"], [2,4,-1]).labels(
        {
            "ph_diff":r_[0:4],
            "ph_overall":r_[0:2],
                    })
all_data["3 echo cpmg"].reorder("t2", first=False).ft(['ph_diff','ph_overall'], unitary=True)
pathways["3 echo cpmg"] = {"ph_diff":1,# fourier conjugate of ?p1
        "ph_overall":-1,# fourier conjugate of ?p1+?p2
        }
show_raw = '3 echo cpmg'
with figlist_var() as fl:
    obs(
        f"spectral width {all_data[show_raw].get_prop('acq_params')['SW_kHz']}~kHz"
    )
    fl.next(f"raw data for {show_raw}")
    fl.image(all_data[show_raw])
    fl.next("show time domain abs", legend=True)
    for thislabel, thisd in all_data.items():
        print("looking at",thislabel)
        thispathway = pathways[thislabel]
        s = select_pathway(thisd, thispathway)
        print("check shape",ndshape(select_pathway(thisd,thispathway)))
        print("t axis",thisd.getaxis('t2')[r_[0,-1]])
        forplot = abs(s)["t2":(None, 150e-3)]
        fl.plot(
            forplot,
            #label=thislabel
            #+ "\n%0.4f" % s.get_prop("acq_params")["carrierFreq_MHz"]
            #+ "\n"
            #+ "noise= %0.2e" % s['t2':(noise_starttime,None)].run(std,'t2').item()
        )
    fl.next("show time domain abs, normalized", legend=True)
    for thislabel, thisd in all_data.items():
        thispathway = pathways[thislabel]
        s = select_pathway(thisd, thispathway)
        forplot = abs(s)["t2":(None, 150e-3)]
        fl.plot(forplot / forplot.max(), label=thislabel)
