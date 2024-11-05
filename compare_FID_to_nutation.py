import pyspecdata as psd
import pyspecProcScripts as prscr
import matplotlib.pyplot as plt
import sympy as sp
import numpy as np
from numpy import r_
import sys
with psd.figlist_var() as fl:
    for searchstr, label, nodename, slice_expansion, apply_first, phase_var in [
            #["241003_27mM_TEMPOL_amp0p2_pm_nutation.h5",
            #    'amplitude = 0.2 nutation 8', 'nutation_8',3,True, False],
            #["241003_27mM_TEMPOL_amp0p2_pm_FID_nutation.h5",
            #    'amplitude = 0.2 FID nutation', 'FID_nutation_1',3,False, False],
            #["241003_27mM_TEMPOL_amp0p05_pm_nutation.h5",
            #    'amplitude = 0.05 nutation', 'nutation_4',10,False, False],
            #["241003_27mM_TEMPOL_amp0p05_pm_FID_nutation.h5",
            #    'amplitude = 0.05 FID nutation', 'FID_nutation_1',10,False, True],
            #["241003_27mM_TEMPOL_amp0p1_pm_nutation.h5",
            #    'amplitude = 0.1 nutation', 'nutation_2',5,False, False],
            #["241003_27mM_TEMPOL_amp0p1_pm_FID_nutation.h5",
            #    'amplitude = 0.1 FID nutation', 'FID_nutation_1',100,False, False],
            #["241003_27mM_TEMPOL_balProbe_nutation.h5",
            #    'amplitude = 0.1 nutation on balanced probe', 'nutation_1',5,False, False],
            #["241003_27mM_TEMPOL_balProbe_FID_nutation.h5",
            #    'amplitude = 0.1 FID nutation on balanced probe', 'FID_nutation_1',15,False, True],
            ["241010_ssProbe_control_onspike_nutation.h5",
                'amplitude = 0.1 no chokes or toroid', 'nutation_1',15,False, False],
            ]:
            s = psd.find_file(
                searchstr,
                exp_type='ODNP_NMR_comp/nutation',
                expno=nodename,
                lookup=prscr.lookup_table,
                fl=fl
            )
            # {{{ set up plots
            int_label = "Integrated a  fit for \n Amplitude: %0.2f"%s.get_prop('acq_params')['amplitude']
            s.set_plot_color_next()
            # }}}
            fl.next("raw %s"%searchstr)
            fl.image(s)
            if ("41" in nodename) or ("FID" in nodename): #4 for amp 0.2 FID for 0.1
                frq_center, frq_half = prscr.find_peakrange(s, peak_lower_thresh = 0.005)
            else:
                frq_center, frq_half = prscr.find_peakrange(s)#, peak_lower_thresh = 0.005)
            print(frq_center)
            print(frq_half)
            #fl.show();quit()

            signal_range = tuple(slice_expansion * r_[-1,1] * frq_half + frq_center)
            signal_pathway = s.get_prop("coherence_pathway")
            if "nScans" in s.dimlabels:
                s.mean("nScans")
            center_of_slice = np.mean(signal_range)
            signal_range_expanded = center_of_slice + 2*r_[-0.5,0.5] * np.diff(
                    signal_range)
            # {{{ apply overall zeroth order correction
            s /= prscr.zeroth_order_ph(
                    prscr.select_pathway(s["t2":signal_range].sum("t2"), signal_pathway)
                    )
            if apply_first:
                # apply first order correction
                s.ift('t2')
                s["t2"] -= s["t2"][0]
                best_shift = prscr.hermitian_function_test(prscr.select_pathway(s["t2":signal_range].C.mean("beta"),signal_pathway))
                #best_shift = s.get_prop("acq_params")["tau_us"]*1e-6
                print(best_shift)
                s.setaxis("t2", lambda x: x - best_shift).register_axis({"t2":0})
                s.ft('t2')
            s = prscr.select_pathway(s["t2":signal_range_expanded], signal_pathway)
            s.ift("t2")
            shift = s * np.exp(-(np.pi**2) * s.fromaxis("t2") ** 2 * (2 * 50**2))
            shift.ft("t2")
            shift = shift.real.run(abs).argmax("t2")
            shift.set_error(None)
            s.ft("t2")
            fl.next("Signal pathway \ ph0 %s"%label,figsize = (6,4))
            fl.image(s["t2":signal_range])
            # }}}
            # {{{ look at phase variation
            mysign = prscr.determine_sign(
                    s,
                    signal_range)
            s *= mysign
            fl.next("check phase variation along indirect %s"%label)
            fl.image(s["t2":signal_range])
            # }}}
            if phase_var:
                for j in range(len(s.getaxis("beta"))):
                    ph0 = prscr.zeroth_order_ph(s["beta",j])
                    s["beta",j] /= ph0
            if 'FID' in nodename:
                s *= mysign
            else:
                signal_pathway = {}
                s = prscr.fid_from_echo(s.set_error(None),signal_pathway)#, peak_lower_thresh = 0.001)
                s *= mysign
                fl.next("Phased and FID sliced %s"%label)
                fl.image(prscr.select_pathway(s['t2':signal_range],signal_pathway))
            s.ift("t2")
            s *= np.exp(-1j*2*np.pi * (shift-center_of_slice) * s.fromaxis("t2"))
            s.ft("t2")
            s = s["t2":signal_range].real.integrate("t2").set_error(None)
            A, R, beta_ninety, beta = sp.symbols("A R beta_ninety beta", real=True)
            if "8" in nodename:
                s["beta",10:14] *= -1
            elif ("4" in nodename) and (s.get_prop("acq_params")["amplitude"] == 0.05):
                s["beta",0:2] *= -1
            elif "balProbe" in searchstr:
                s = s["beta":(None,170e-6)]
            fl.next(int_label,figsize = (6,4))
            fl.plot(s, "o")#, label = label)
            f = psd.lmfitdata(s)
            print(type(A * sp.exp(-R * beta) * sp.sin(beta / beta_ninety * sp.pi / 2)**3))
            if 'FID' in nodename:
                f.functional_form = (
                    A * sp.exp(-R * beta) * sp.sin(beta / beta_ninety * sp.pi / 2)
                )
            else:
                f.functional_form = (
                    A * sp.exp(-R * beta) * sp.sin(beta / beta_ninety * sp.pi / 2)**3
                )
            f.set_guess(
                A=dict(
                    value=s.data.max() * 1.2,
                    min=s.data.max() * 0.8,
                    max=s.data.max() * 1.5,
                ),
                R=dict(value=3e3, min=0, max=3e4),
                beta_ninety=dict(value=1.5e-5, min=0, max=1),
            )
            f.fit()
            fit = f.eval(100)
            fit.copy_props(s)
            fl.plot(fit)
            plt.xlabel(r"$\beta$ / $\mathrm{\mu s \sqrt{W}}$")
            beta_90 = f.output("beta_ninety") * 1e6
            if 'FID' in nodename:
                thiscolor = "tab:orange"
                plt.axvline(beta_90, ls = ":", alpha = 0.5, color = thiscolor)
                plt.text(
                    beta_90+5,
                    100000,
                    r"$FID \beta_{90} = %f \mathrm{\mu s \sqrt{W}}$" % beta_90,
                    color = thiscolor,
                )
            else:
                thiscolor = "tab:blue"
                plt.axvline(beta_90, ls = ":", alpha = 0.5, color = thiscolor)
                plt.text(
                    beta_90+80,
                    100000,
                    r"$SE \beta_{90} = %f \mathrm{\mu s \sqrt{W}}$" % beta_90,
                    color = thiscolor,
                )
            psd.gridandtick(plt.gca())

