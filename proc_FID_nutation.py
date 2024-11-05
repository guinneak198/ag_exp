import pyspecdata as psd
import pyspecProcScripts as prscr
import numpy as np
import matplotlib.pyplot as plt


def clock_correct(s, axis_along, direct="t2", max_cyc=0.5):
    for_correct = s.C
    Delta = np.diff(s[axis_along][np.r_[0, -1]]).item()
    correction_axis = psd.nddata(np.r_[-0.5:0.5:300j] * max_cyc / Delta, "correction")
    for_correct = for_correct * np.exp(
        -1j * 2 * np.pi * correction_axis * for_correct.fromaxis(axis_along)
    )
    # {{{ determine the best sign flip for each correction
    for j in range(for_correct.shape["correction"]):
        thesign = prscr.determine_sign(for_correct["correction", j])
        for_correct["correction", j] *= thesign
    # }}}
    for_correct.sum(direct)
    return for_correct.sum(axis_along).run(abs).argmax("correction").item()


disprange = (-500, 500)
signal_range = (-250, -50)

with psd.figlist_var() as fl:
    s = psd.find_file(
        "240805_amp1_FID_nutation.h5",
        exp_type="ODNP_NMR_comp/nutation",
        expno="FID_nutation_2",
        lookup=prscr.lookup_table,
    )
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
    fl.next("Raw data", fig=fig)
    fig.suptitle("Single Pulse nutation")
    fl.image(s.C["t2":disprange], ax=ax1)
    ax1.set_title("Raw Data")
    total_corr = 0
    og_signs = prscr.determine_sign(
        prscr.select_pathway(s["t2":signal_range], s.get_prop("coherence_pathway"))
    )
    for j in range(5):
        corr = clock_correct(
            prscr.select_pathway(s, s.get_prop("coherence_pathway"))
            * og_signs
            * np.exp(-1j * 2 * np.pi * total_corr * s.fromaxis("p_90")),
            "p_90",
        )
        total_corr += corr
    s *= np.exp(-1j * 2 * np.pi * total_corr * s.fromaxis("p_90"))
    for j in range(len(s.getaxis("p_90"))):
        ph0 = prscr.zeroth_order_ph(
            prscr.select_pathway(
                s["p_90", j]["t2":signal_range], s.get_prop("coherence_pathway")
            )
        )
        s["p_90", j] /= ph0
    my_signs = prscr.determine_sign(
        prscr.select_pathway(s["t2":signal_range], s.get_prop("coherence_pathway"))
    )
    s *= my_signs
    s = prscr.fid_from_echo(s, s.get_prop("coherence_pathway"))
    fl.image(s, ax=ax2)
    ax2.set_title("Phased and FID sliced")
    if og_signs.data[3] < 1:
        s *= -og_signs
    else:
        s *= og_signs
    fl.image(s, ax=ax3)
    ax3.set_title("Sign Flipped Back")
    s = prscr.select_pathway(s, s.get_prop("coherence_pathway"))
    s = s.real.integrate("t2")
    fl.next("Integrated")
    fl.plot(s, "o")
