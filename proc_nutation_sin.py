from pylab import *
from pyspecdata import *
from scipy.optimize import minimize
from pyspecProcScripts import *
from pyspecProcScripts import fid_from_echo, lookup_table
from sympy import symbols, Symbol, latex
import sympy as sp
from numpy import *
import matplotlib as mpl
fl = figlist_var()
t2 = symbols('t2')
logger = init_logging("info")
def clock_correct(s, axis_along, direct="t2", max_cyc=0.5):
    for_correct = s.C
    Delta = np.diff(s[axis_along][np.r_[0, -1]]).item()
    correction_axis = nddata(np.r_[-0.5:0.5:300j] * max_cyc / Delta, "correction")
    for_correct = for_correct * np.exp(
        -1j * 2 * np.pi * correction_axis * for_correct.fromaxis(axis_along)
    )
    # {{{ determine the best sign flip for each correction
    for j in range(for_correct.shape["correction"]):
        thesign = determine_sign(for_correct["correction", j])
        for_correct["correction", j] *= thesign
    # }}}
    for_correct.sum(direct)
    return for_correct.sum(axis_along).run(abs).argmax("correction").item()
signal_range = (-250,250)
plot_DCCT=False
for searchstr,exptype,nodename, label  in [
    #['240801_27mM_TEMPOL_amp1_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_4', 'amplitude = 1.0'],
    #['240801_27mM_TEMPOL_amp1_nutation','ODNP_NMR_comp/nutation','nutation_5', 'amplitude = 1.0'],
    #['240801_27mM_TEMPOL_amp0p1_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_1', 'amplitude = 0.1'],
    #['240801_27mM_TEMPOL_amp0p1_nutation','ODNP_NMR_comp/nutation','nutation_3', 'amplitude = 0.1'],
    #['240802_amp0p1_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_3', 'amplitude = 0.1'],
    #['240802_amp1_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_1', 'amplitude = 1'],
    #['240802_amp0p2_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_2', 'amplitude = 0.2'],
    #['240802_amp0p2_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_1', 'repetition = 0.8s'],
    #['240802_amp0p2_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_3', 'repetition = 5'],
    #['240802_amp0p2_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_4', 'repetition = 10s'],
    #['240805_amp0p05_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_1', 'FID'],
    #['240805_amp0p05_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_1', 'SE'],
    #['240805_amp0p1_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_1', 'FID'],
    #['240805_amp0p1_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_1', 'SE'],
    #['240805_amp0p2_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_1', 'FID'],
    #['240805_amp0p2_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_1', 'SE'],
    ['240805_amp1_27mM_TEMPOL_FID_nutation','ODNP_NMR_comp/nutation','FID_nutation_1', 'FID'],
    ['240805_amp1_27mM_TEMPOL_nutation','ODNP_NMR_comp/nutation','nutation_1', 'SE'],
    ]:
    s = find_file(searchstr,exp_type=exptype,expno=nodename, lookup = lookup_table)
    signal_pathway = s.get_prop("coherence_pathway")
    label += "amplitude = %s"%str(s.get_prop('acq_params')['amplitude'])  
    fl.next('Raw Freq %s'%label)
    fl.image(select_pathway(s,s.get_prop('coherence_pathway')))
    s.ift('t2')
    fl.next('Raw Time %s'%label)
    fl.image(s)
    s.ft('t2')
    if 'nScans' in s.dimlabels:
        s.mean('nScans')
    rough_int = select_pathway(s['t2':(-250,250)],signal_pathway).C.real.integrate('t2')
    fl.next('Integrate raw')
    fl.plot(rough_int,  label = label)
    #s_fullsw = s.C
    #s.ift('t2')
    #s.set_units('t2','s')
    #fl.basename = ''
    #s.ft('t2')
    mysgn = determine_sign(
            select_pathway(s["t2":signal_range],
                s.get_prop('coherence_pathway'))
            )
    total_corr = 0
    for j in range(5):
        corr = clock_correct(select_pathway(s,s.get_prop('coherence_pathway'))
                * mysgn
                *np.exp(-1j*2*pi*total_corr*s.fromaxis('beta')),
                "beta"
                )
        total_corr += corr
    s *= np.exp(-1j*2*pi*total_corr*s.fromaxis('beta'))
    for j in range(len(s.getaxis('beta'))):
        ph0 = zeroth_order_ph(
                select_pathway(
                    s['beta',j]['t2':signal_range], s.get_prop('coherence_pathway')
                    )
                )
        s['beta',j] /= ph0
    mysigns = determine_sign(
            select_pathway(s["t2":signal_range],
                s.get_prop('coherence_pathway'))
            )
    if label == 'amplitude = 1':
        s *= -mysgn
    else:
        s *= mysgn
    fl.next('with sign flip %s'%label)
    fl.image(s)
    s.ift('t2')
    s['t2'] -= s.getaxis('t2')[0]
    s.setaxis('t2', lambda x: x - s.get_prop('acq_params')['tau_us']*1e-6).register_axis({'t2':0})
    s /= zeroth_order_ph(select_pathway(s['t2':0.0],signal_pathway))
    s = s['t2':(0,None)]
    s *= 2
    s['t2',0] *= 0.5
    #fl.basename = label
    #s = fid_from_echo(s,signal_pathway,fl = fl)
    s.ft('t2')
    # {{{ correl align
    s.ift(list(s.get_prop('coherence_pathway').keys()))
    opt_shift, sigma, mask_func = correl_align(
            s*mysgn,
            indirect_dim = 'beta',
            signal_pathway = s.get_prop('coherence_pathway'),
            sigma = 50)
    s.ift('t2')
    #s *= np.exp(-1j*2*pi*opt_shift*s.fromaxis('t2'))
    s.ft(list(s.get_prop('coherence_pathway').keys()))
    s.ft('t2')
    s *= mysigns
    fl.next('phased %s'%label)
    fl.image(s)
    fl.next('int after phase')
    fl.plot(select_pathway(s['t2':signal_range],signal_pathway).C.real.integrate('t2'),label = label)
    ## {{{align
    #s.ift(list(signal_pathway))
    #opt_shift,sigma,my_mask = correl_align(
    #        s, indirect_dim='indirect',
    #        sigma = 10,
    #        signal_pathway=signal_pathway)
    #s.ift('t2')
    #s *= np.exp(-1j*2*pi*opt_shift*s.fromaxis('t2'))
    #s.ft(list(signal_pathway))
    #s.ft('t2')
    ## }}}
    #dcct = s.C
    #s = select_pathway(s,signal_pathway)
    ## {{{ DCCT
    #if plot_DCCT:
    #    dcct.rename('indirect','$t_{90}\sqrt{P_{tx}}$')
    #    dcct['$t_{90}\sqrt{P_{tx}}$'] *= (39.4/4.52)
    #    dcct_kwargs = dict(
    #            max_coh_jump = {'ph1':1},
    #            total_spacing = 0.1,
    #            label_spacing_multiplier = -5,
    #            LHS_pad = 0.06,
    #            RHS_pad = 0.01,
    #            allow_for_ticks_default = 40,
    #            bottom_pad = 0.25,
    #            text_height = 8)
    #    dcct.reorder(['ph1','$t_{90}\sqrt{P_{tx}}$','t2'])
    #    dcct['$t_{90}\sqrt{P_{tx}}$',12:] *= -1 #using the fid from echo made everything the same sign but idx 12 is where the flip should be
    #    # AG tried using determine sign but it didn't recognize the correct flip idx
    #    dcct.set_units('$t_{90}\sqrt{P_{tx}}$','\mu{s}\sqrt{W}')
    #    DCCT(dcct,
    #            this_fig_obj = figure(figsize=(6,4)),
    #            plot_title = fl.current,
    #            **dcct_kwargs)
    #    savefig('nutation_DCCT.png',
    #            transparent=True,
    #            bbox_inches = 'tight',
    #            pad_inches = 0.1)
    #    fl.show();quit()
    ## }}}    
    #s.rename('indirect','p_90')    
    #s = s['p_90',1:]
    #for_90 = s.C
    #s = s.real.integrate('t2')
    #s['p_90'] *= (39.4/4.52) #convert to t90*sqrt(P)
    #A, B, omega, phi, p_90 = symbols("A B omega phi p_90",real=True)
    #f = lmfitdata(s)
    #f.functional_form = B+(A*sp.sin(omega*p_90 +phi)) #everything is positive so I am adding B to lift the fit
    #f.set_guess(
    #        A = dict(value = 2.5e4, min = 1e3, max = 3e4),
    #        B = dict(value = 2e4, min = 0, max = 1e6),
    #        omega = dict(value =90, min =80, max = 150),
    #        phi = dict(value = -0.5, min = -pi, max = pi)
    #        )
    ##f.settoguess()
    ##guess = f.eval()
    ##fl.next('guess')
    ##fl.plot(s,'ko')
    ##fl.plot(guess)
    #f.fit()
    #fit = f.eval()
    #B = f.output('B')
    #A = f.output('A')
    #omega = f.output('omega')
    #phi = f.output('phi')
    #fl.next('')
    #s.data -= B #shift the data back down to center about 0
    #fit -= B
    #fl.plot(s,'ko')
    #fl.plot(fit,color = 'orange',alpha = 0.5)
    #print(fit.argmax('p_90'))
    #print(omega)
    #print(B)
    #print(A)
    #print(phi)
    #crossing = (1/omega)*(arcsin((-B/A)-phi))
    #print(crossing/2)
    #plt.ylabel(None)
    #plt.xlabel('$t_{90}\sqrt{P_{tx}} / \mu s\sqrt{W}$')
    #plt.axvline(41.96,ls = ":", color = 'k',alpha = 0.3)
    #plt.text(72,9e3,"$t_{90}\sqrt{P_{tx}} = 41.96 \mu s\sqrt{W}$",fontsize = 8)
fl.show()

