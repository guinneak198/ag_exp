from Instruments import AFG
from pyspecdata import getDATADIR
import time
import SpinCore_pp as sc
from datetime import datetime
from scipy import signal
# {{{ make filename
description = '3p9kHz_filter'
date = datetime.now().strftime('%y%m%d')
output = date+'_'+description+'.h5'
# }}}
#{{{ AFG settings
#Make a list of the desired output frequencies
freq_list = np.linspace(14.8766e6,14.9234e6,300) #Hz
amplitude = 0.01 #desired Vpp
# }}}
#{{{ Spincore settings
SW_kHz = 3.9
carrierFreq_MHz = 14.9 
adcOffset = 42
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 25
nPoints = 1024*2
acq_time = nPoints/SW_kHz + 1.0
tau = 10.0 + acq_time*1e3*(1./8.)
data_length = 2*nPoints
#}}}
with AFG() as a:
    a.reset()
    # set amplitude on AFG
    a[0].ampl = amplitude
    for j, frq in enumerate(freq_list):
        a[0].output = True #output the amplitude
        #output sine wave at the programmed frequency and amplitude
        a.sin(ch=1, V = amplitude, f = frq) 
        time.sleep(2)
        for x in range(nScans):
            # {{{ configure SpinCore
            sc.configureTX(adcOffset, carrierFreq_MHz, tx_phases, 1.0, nPoints)
            acq_time = sc.configureRX(SW_kHz, nPoints, 1, 1, 1)
            sc.init_ppg();
            # }}}
            # {{{ ppg to generate the SpinCore Data
            sc.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay',tau),
                ('delay',10.0),
                ('acquire',acq_time),
                ('delay',1e4),
                ('jumpto','start')
                ])
            # }}}
            sc.stop_ppg();
            sc.runBoard();
            # {{{ grab data for the single capture as a complex value
            raw_data = (
                    sc.getData(data_length, nPoints, 1, 1)
                    .astype(float)
                    .view(complex)
                    )
            # }}}
            # {{{ if this is the first scan of the set frequency, then
            #     allocate an array to drop the data into, and assign the
            #     axis coordinates, etc.
            if x == 0:
                time_axis = np.linspace(0.0,acq_time*1e-3,raw_data.size)
                data = (
                        ps.ndshape(
                            [raw_data.size,nScans],
                            ['t','nScans']
                            )
                        .alloc(dtype=np.complex128)
                        .setaxis('t',time_axis)
                        .set_units('t','s')
                        .setaxis('nScans',r_[0:nScans])
                        .name('signal %f kHz'%frq/1e3)
                        )
                # }}}
            data['nScans',x] = raw_data # drop the data into appropriate index
            sc.stopBoard();
        data.set_prop('afg_frq', frq/1e3) #set an acquisition parameter to 
        #                                   the set frequency in kHz
        data.name('afg_%d'%frq)    
        nodename = data.name()
        data.hdf5_write(output,directory = 'ODNP_NMR_comp/noise_tests')
