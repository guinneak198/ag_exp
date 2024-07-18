from pyspecdata import *
from pyspecProcScripts import *
import numpy as np
fl = figlist_var()
for searchstr,exptype,nodename,postproc,freq_slice in [
    ['240715_27mM_TEMPOL_test_generic_FID','ODNP_NMR_comp/FID','FID_2',
        'None',(-800,800)]
    ]:
    s = find_file(searchstr,exp_type=exptype,expno=nodename)
    s.ft(['ph1'],unitary = True)
    s.ft('t2',shift = True)
    fl.next('Raw f domain averaged scans')
    fl.image(s.C.mean('nScans'))
    s.ift('t2')
    s.set_units('t2','s')
    fl.next('Raw t domain averaged scans')
    fl.image(s.C.mean('nScans'))
    for_herm = s['ph1',1].C
    s.ft('t2')
    s = s['t2':(-800,800)]
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
    best_shift = 5e-3
    s.setaxis('t2', lambda x: x - best_shift).register_axis({'t2':0})
    ph0 = zeroth_order_ph(s['t2':(-500,500)].C.sum('t2'))
    s /= ph0
    s.ft('t2')
    fl.next('phased')
    fl.image(s)
    s.ift('t2')
    fl.next('time domain phased')
    fl.image(s)
    filter_t_const = 10e-3
    apo_fn = np.exp(-abs((s.fromaxis('t2')-s.get_prop('acq_params')['tau_us']*1e-6))/filter_t_const)
    s *= apo_fn
    s.ft('t2')
    s.mean('nScans')
    fl.next('apodized and averaged')
    fl.image(s)
    s.ift('t2')
    s = s['t2':(0,None)]
    s *= 2
    s['t2':0] * 0.5
    s.ft('t2')
    fl.next('FID slice the phased, apo, and averaged data')
    fl.image(s)

    fl.show()

