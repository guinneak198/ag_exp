from pylab import *
from pyspecdata import *
from scipy.optimize import minimize
from pyspecProcScripts import *
from sympy import symbols
from numpy import *
fl = fl_mod()
t2 = symbols('t2')
logger = init_logging("info")
max_kHz = 3.9
signal_pathway = {'ph1':0,'ph2':1}
for searchstr,exptype,nodename,postproc,freq_slice in [
    ['230623_pR_batch230605_N187_a_nutation_1','ODNP_NMR_comp/nutation','nutation',
        'spincore_nutation_v3',(-500,450)]
    ]:
    s = find_file(searchstr,exp_type=exptype,expno=nodename,postproc=postproc,
            lookup=lookup_table,fl=fl)
    s_fullsw = s.C
    s.ift('t2')
    s.reorder(['ph1','ph2','indirect','t2'])
    t_max = s.getaxis('t2')[-1]
    rx_offset_corr = s['t2':(0.75*t_max,None)] #should be quarter of t_slice onward
    rx_offset_corr = rx_offset_corr.mean(['t2'])
    s -= rx_offset_corr
    s.ft('t2')
    fl.next('raw')
    fl.image(s.C.mean('nScans'))
    d = s_fullsw
    if 'amp' in s.dimlabels:
        plen = s.get_prop('acq_params')['p90_us']*1e-6
        logger.info(strm('pulse length is:',plen))
    s = s['t2':freq_slice]
    #s['indirect':-1] *= -1
    s.ift('t2')
    s.set_units('t2','s')
    best_shift = 0.0035
    #s.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    #{{{zeroth order phasing
    s /= zeroth_order_ph(select_pathway(s['t2':0].C.mean('nScans'),signal_pathway))
    s.ft('t2')
    fl.next('phase corrected')
    fl.image(s.C.mean('nScans'))
    #}}}
    s.ift('t2')
    s = s['t2':(0,None)]
    s *= 2
    s['t2':0] *= 0.5
    s.ft('t2')
    fl.next('phased')
    fl.plot(select_pathway(s.C.mean('nScans'),signal_pathway))
     # {{{ do the centering before anything else!
    # in particular -- if you don't do this before convolution, the
    # convolution doesn't work properly!
    d = s.C
    d.ift('t2')
    d.set_units('t2','s')
    fl.next('time')
    fl.plot(select_pathway(d.C,signal_pathway),alpha = 0.25)
    filter_t_const = 10e-3
    apo_fn = exp(-abs((d.fromaxis('t2')-d.get_prop('acq_params')['tau']*1e-6))/filter_t_const)
    fl.plot(apo_fn*abs(d.C).max(),human_units = False)
    d *= apo_fn
    d /= zeroth_order_ph(select_pathway(d,signal_pathway))
    d.ft('t2')
    fl.next('apodized')
    fl.plot(select_pathway(d,signal_pathway))
    #}}}
    #{{{ selecting coherence and convolving
    s = select_pathway(d,signal_pathway)
    #}}}
    if 'amp' in s.dimlabels:
        s.setaxis('amp',lambda x:x*plen)
        s.set_units('amp','s')
        ind_dim = '\\tau_p a'
        s.rename('amp',ind_dim)
    elif 'p_90' in s.dimlabels:
        ind_dim = 'p_90'
    elif 'indirect' in s.dimlabels:
        p_90 = s.getaxis('indirect')
        s.setaxis('indirect',p_90)
        s.rename('indirect','p_90')
        ind_dim = 'p_90'
    else:
        raise ValueError("not sure what the indirect dimenison is!!")
    for_90 = s.C.mean('nScans')
    fl.next('p90')
    for j in range(3):
        fl.plot(for_90['p_90',j],label = '%d'%j)
    maxes = []
    for j in range(len(for_90.getaxis('p_90'))):
        thismax = abs(for_90['p_90',j]).C.max().real.item()
        if j ==2:
            print("last p90 should be inverted")
            thismax = for_90['p_90',j].C.min().real.item()
        maxes.append(thismax)
    fl.next('line for p90')
    d = nddata(maxes,[-1],['p90'])
    d.setaxis('p90',for_90.getaxis('p_90'))
    fl.plot(d, 'o')
    fit = d.polyfit('p90',order = 1)
    p90_fine = nddata(np.linspace(6,d.getaxis('p90')[-1],300),'p90')
    fit_fine = p90_fine.C.eval_poly(fit,'p90')
    fl.plot(fit_fine,label = 'fit')
    fl.show();quit()
