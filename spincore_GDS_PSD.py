import numpy as np
from numpy import r_
from pyspecdata import *
from pylab import *
import os
import sys
from itertools import cycle
matplotlib.rcParams['legend.fontsize'] ='xx-small'
matplotlib.rcParams['legend.labelspacing'] = 0.2 
rcParams['savefig.transparent'] = True
colors = cycle(['blue','orange','red','green','magenta','lime','brown','black','pink'])
colors = cycle(['blue','red','orange','green','magenta','lime','purple','black','hotpink'])
fl = figlist_var()
thisgain = (13.8461e-3/49.586e-6)**2
T = 273.15 + 19.
width = 0.2e5
width = 0.2e6
for filename, label, MSPS, measure, width,carrier in [
        ('230928_probe_split_2a_20000kHz.h5','SC',4.075e-8,'Spincore',0.8e5,14.9e6),
        ('230928_probe_split_2a.h5','10. 18 mHZ',4.04e-8,'GDS',0.8e5,14.9e6),
        #('230925_probe_7_2mV.h5','GDS',4.04e-8,'GDS',0.8e5,14.9e6),
        #('230705_signal_100MSPS_20mV_10000kHz.h5','Spincore',2.11398e-8,'Spincore',thisgain,14.8e6),
        #('230705_100MSPS_signal_20mV.h5','GDS',100,'GDS',thisgain,0),
        #('230705_5GSPS_10mV_signal.h5','5 GSPS GDS',700,' GDS',gain3),
        #('230705_100ns_10mV_signal.h5','15 GSPS GDS',700,'GDS',thisgain),
        #('230705_5GSPS_50mV_signal.h5','5 GSPS GDS 50 mV',700,' GDS',gain3),
    ]:    
    if measure == 'Spincore':
        s = find_file(filename, exp_type = 'ODNP_NMR_comp/Echoes', expno = 'signal')
        s.rename('nScans','capture')
        acq_time = diff(s.getaxis('t')[r_[0,-1]])[0]
        s *= MSPS
        s.set_units('t','s')
        u = s['t':(0,None)].C
    else:
        s = nddata_hdf5(filename+'/accumulated_230928', directory = getDATADIR(exp_type = 'ODNP_NMR_comp/noise_tests'))
        s.set_units('t','s')
        s = s['ch',0]
        u = s.C
    acq_time = diff(s.getaxis('t')[r_[0,-1]])[0]    
    u_acq_time = diff(u.getaxis('t')[r_[0,-1]])[0]
    s.ft('t',shift = True)
    thiscolor = next(colors)    
    #s = s['capture',0].C
    #u = u['capture',0].C
    if measure == 'GDS':
        s['t':(None,0)] *= 0# = s['t':(0,None)]
        s *= 2
        s['t':0] *= 0.5
        s.ift('t')
        #s *= exp(-1j*2*pi*14.8e6*s.fromaxis('t'))
        s.ft('t')
    #s = s['t':(-4.5e6,4.5e6)]
    s /= sqrt(2)
    s = abs(s)
    s.mean('capture')
    s = s**2
    s /= acq_time
    s /= 50
    s /= thisgain
    #s *= 1e2
    u_filt = u.C
    u.ft('t',shift = True)
    if measure == 'GDS':
        u['t':(None,0)] *= 0
        u *= 2
        u['t':0] *= 0.5
        u.ift('t')
    #    u *= exp(-1j*2*pi*14.8e6*u.fromaxis('t'))
        u.ft('t')
   # u = u['t':(-4.5e6,4.5e6)]
    u /= sqrt(2)
    u = abs(u)
    u.mean('capture')
    u = u**2
    u /= u_acq_time
    u /= 50
    u /= thisgain
    #u *= 1e2
    u_filt.ft('t',shift = True)
    if measure == 'GDS':
        u_filt['t':(None,0)] *= 0
        u_filt *= 2
        u_filt['t':0] *= 0.5
        u_filt.ift('t')
    #    u_filt *= exp(-1j*2*pi*14.8e6*u_filt.fromaxis('t'))
        u_filt.ft('t')
   # u_filt = u_filt['t':(-4.5e6,4.5e6)]    
    u_filt /= sqrt(2)
    u_filt = abs(u_filt)
    u_filt.mean('capture')
    u_filt = u_filt**2
    u_filt.convolve('t',width,enforce_causality = False)
    u_filt /= 50
    u_filt /= u_acq_time
    u_filt /= thisgain
    #u_filt *= 1e2
    s /= k_B*T
    u /= k_B*T
    u_filt /= k_B*T
    s.name('$S(\\nu)$').set_units('W/Hz')
    u.name('${S(\\nu)}/{k_{B}T}$')
    u_filt.name('${S(\\nu)}/{k_{B}T}$')
    if measure == 'Spincore':
        s.ift('t')
        s.run(conj)
        s.ft('t')
        s.setaxis('t',lambda x:x+carrier)
        u.ift('t')
        u.run(conj)
        u.ft('t')
        u.setaxis('t',lambda x:x+carrier)
        u_filt.ift('t')
        u_filt.run(conj)
        u_filt.ft('t')
        u_filt.setaxis('t',lambda x:x+carrier)
    else:
        s = s['t':(0,None)]
        u_filt = u_filt['t':(0,None)]
    fl.next('Aliasing with 20 MHz SC bandwidth')
    fl.plot(s, label = None, color=thiscolor,alpha = 0.1, plottype = 'semilogy')#,human_units = False),
    fl.plot(u_filt, label = label, color=thiscolor,alpha = 0.3, plottype = 'semilogy')#,human_units=False)
    plt.axhline(1)
    plt.ylim(0.005,34e3)
    plt.axvline(14.9)
fl.show()

