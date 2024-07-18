from sympy import symbols
import sympy as sp
from itertools import cycle
from pylab import axhline, title, gca, axvline, ylabel, tight_layout, legend
import matplotlib.pyplot as plt
from pyspecProcScripts import *
from pyspecdata import (
    nddata,
    r_,
    find_file,
    lmfitdata,
    figlist_var,
    k_B,
    gammabar_H,
    hbar,
    ndshape
)
from numpy import std, sqrt, pi, mean, sinc, conj, diff, log10, exp
import numpy as np
signal_pathway = {'ph1':1,'ph2':-2}#{'ph1':0,'ph2':1}
fl = figlist_var()
for searchstr,exptype,nodename,postproc,freq_slice in [
    ['240715_27mM_TEMPOL_test_nutation','ODNP_NMR_comp/nutation','nutation_6',
        'None',(-800,800)]
    ]:
    s = find_file(searchstr,exp_type=exptype,expno=nodename)
    s.set_units('p_90','s')
    s.ft(['ph1','ph2'],unitary = True)
    s.reorder(['nScans','ph1','ph2', 'p_90'])
    s.ft('t2',shift = True)
    s.ift('t2')
    s.set_units('t2','s')
    for_herm = select_pathway(s,signal_pathway)
    s.ft('t2')
    s = s['t2':freq_slice]
    fl.next('for herm sign flip')
    #for_herm *= mysgn
    fl.image(for_herm)
    s.ift('t2')
    ## {{{ phasing
    s['t2'] -= s.getaxis('t2')[0]
    signflip = for_herm.C.ft('t2')['t2':(-500,500)]
    idx = abs(signflip).mean_all_but('t2').data.argmax()
    signflip = signflip['t2',idx]
    ph0 = zeroth_order_ph(signflip)
    signflip /= ph0
    signflip.run(np.real)
    signflip /= abs(signflip)
    for_herm /= signflip
    for_herm.mean_all_but('t2')
    best_shift = hermitian_function_test(for_herm,fl=fl)
    best_shift = s.get_prop('acq_params')['tau_us']*1e-6#3.5e-3
    s.setaxis('t2', lambda x: x - best_shift).register_axis({'t2':0})
    #ph0 = zeroth_order_ph(s['t2':(-500,500)].C.sum('t2'))
    #s /= ph0
    # }}}
    ## {{{ FID slice
    #s = s['t2':(0,None)]
    #s *= 2
    #s['t2',0] *= 0.5
    s.ft('t2')
    fl.next('phased')
    fl.image(s)
    fl.next('phased and averaged')
    fl.image(s.C.mean('nScans'))
    s.ift('t2')
    fl.next('time domain phased')
    fl.image(s)
    filter_t_const = 10e-3
    apo_fn = exp(-abs((s.fromaxis('t2')-s.get_prop('acq_params')['tau_us']*1e-6))/filter_t_const)
    s *= apo_fn
    #s /= zeroth_order_ph(select_pathway(s['t2':0],signal_pathway))
    # }}}
    #lambda_L = fit_envelope(s.C.mean('nScans'), fl=fl)
    s.ft('t2')
    fl.next('apodized and averaged')
    s.mean('nScans')
    fl.image(s)
    s.ift('t2')
    s = s['t2':(0,None)]
    s *= 2
    s['t2':0] * 0.5
    s.ft('t2')
    #s.ift('t2')
    #ph0 = zeroth_order_ph(s['t2':(-500,500)].C.sum('t2'))
    #s /= ph0
    #s.ft('t2')
    fl.next('FID slice the phased, apo, and averaged data')
    fl.image(s)
    s = select_pathway(s,signal_pathway)
    fl.next('pcolor')
    s.pcolor()
    fl.show();quit()
    #s = s['ph1',1]['ph2',-2].C + s['ph1',-1]['ph2',0].C
    #d = s.real.integrate('t2')
    #print(ndshape(d))
    #fl.next('integrate the FID slice')
    #fl.plot(d,'o')
    #fl.show();quit()
    ##s.mean('nScans')
    #fl.next('apodized')
    #fl.image(s.C.mean('nScans'))
    #fl.show();quit()
    # {{{ roughly align
    #for_sign = s['ph1',1]['ph2',-2].C + s['ph1',-1]['ph2',0].C
    mysgn = determine_sign(select_pathway(s,signal_pathway))
    #matched = (select_pathway(s,signal_pathway)*mysgn).ift('t2')
    #matched *= exp(-pi*lambda_L*matched.fromaxis('t2'))
    #matched.ft('t2')
    #frq_atmax = matched.real.argmax('t2')
    #s.ift('t2')
    #t2 = s.fromaxis('t2')
    #s *= exp(-1j*2*pi*frq_atmax*t2)
    #s.ft('t2')
    #fl.next('simple shift')
    #fl.image(s)
    # }}}
    # {{{apply correlation alignment
    s.ift(list(signal_pathway))
    s *= mysgn
    fl.next('before alignment')
    fl.image(select_pathway(s,signal_pathway))
    opt_shift,sigma,my_mask = correl_align(
            s,#*mysgn, 
            indirect_dim='p_90',
            sigma = 50,
            signal_pathway=signal_pathway)
    s.ift('t2')
    s *= np.exp(-1j*2*pi*opt_shift*s.fromaxis('t2'))
    s.ft(list(signal_pathway))
    s = s['t2':(0,None)]
    s *= 2
    s['t2':0] *= 0.5
    s.ft('t2')
    fl.next('after alignment')
    fl.image(select_pathway(s,signal_pathway))
    s *= mysgn
    fl.next('after sign flip')
    fl.image(select_pathway(s,signal_pathway))
    s = select_pathway(s,signal_pathway)
    # }}}
    fl.next('line for p90')
    s.setaxis('p_90',s.get_prop('prog_p90s'))
    s = s.real.mean('nScans').integrate('t2')
    #s = s['nScans',1].real.integrate('t2')
    #s['p_90'] *= 39.4/4.52
    fl.plot(s,'o',label = 'actual p90s')
    # {{{ Fit
    #A, omega, p_90 = symbols("A omega p_90",real=True)
    #f = lmfitdata(s)
    #f.functional_form = (A*sp.sin(omega*p_90))
    #f.set_guess(
    #        A = dict(value = s.data.max(), min = s.data.max()/1.2, max = s.data.max()*2),
    #        omega = dict(value = 5e4, min =0, max = 10e6),
    #        )
    #f.settoguess()
    #fl.plot(f.eval(100),color = 'red')
    #f.fit()
    #fit = f.eval(100)
    #fl.plot(fit)
    #fl.next('Fixed phasing')
    #fl.plot(s,'o')
    ##fl.plot(fit)
    #t90_sqrt_P = fit.argmax('p_90').item()
    #print(t90_sqrt_P*1e6/(39.4/4.52))
    ##plt.axvline(t90_sqrt_P*1e6, label = '$t_{90}\sqrt{P}$ = %0.3f$\mu$s$\sqrt{W}$'%(t90_sqrt_P*1e6))
    ##plt.xlabel('$t_{90}\sqrt{P}$')
    ##plt.legend()
    ## }}}
    fl.show()

