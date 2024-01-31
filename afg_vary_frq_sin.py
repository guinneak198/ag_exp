from Instruments import *
from pyspecdata import *
import time
import SpinCore_pp
from datetime import datetime
from serial.tools.list_ports import comports
import serial
from scipy import signal
print("These are the instruments available:")
SerialInstrument(None)
print("done printing available instruments")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")

with SerialInstrument('AFG-2225') as s:
    print((s.respond('*idn?')))
#{{{ Spincore settings
SW_kHz = 3.9
adcOffset = 42
carrierFreq_MHz = 14.9
tx_phases = r_[0.0,90.0,180.0,270.0]
SC_amplitude = 1.0
nScans = 25
nEchoes = 1
phase_cycling = False
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
p90 = 4.0
deadtime = 10.0
repetition = 1e4
nPoints = 1024*2
acq_time = nPoints/SW_kHz + 1.0
tau_adjust = 0.0
deblank = 1.0
tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust
pad = 0
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = SC_amplitude
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = deblank
acq_params['tau_us'] = tau
acq_params['pad_us'] = pad 
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps#}}}
data_length = 2*nPoints*nEchoes*nPhaseSteps
#}}}
#{{{ AFG settings
freq_list = np.linspace(14.8766e6,14.9234e6,300)
amplitude = 0.01 #desired Vpp
output = date+'_'+'afg_sc_10mV_3p9kHz_wide_a.h5'
with AFG() as a:
    a.reset()
    a[0].ampl = amplitude
    for j, frq in enumerate(freq_list):
        a[0].output = True
        frq_kHz = frq/1e3 
        print("Frequency is:",frq)
        a.sin(ch=1, V = amplitude, f = frq)
        print("sin wave made")
        time.sleep(2)
        for x in range(nScans):
            print("configuring")
            SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, SC_amplitude, nPoints)
            print("acq stuff")
            acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
            acq_params['acq_time_ms'] = acq_time
            # acq_time is in msec!
            SpinCore_pp.init_ppg();
            print("initing") 
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay',tau),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
            SpinCore_pp.stop_ppg();
            SpinCore_pp.runBoard();
            raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps)
            raw_data.astype(float)
            data_array = []
            data_array[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
            dataPoints = int(np.shape(data_array)[0])
            if x == 0:
                time_axis = np.linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
                data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=np.complex128)
                data.setaxis('t',time_axis).set_units('t','s')
                data.setaxis('nScans',r_[0:nScans])
                data.name('signal %f kHz'%frq_kHz)
                data.set_prop('acq_params',acq_params)
            data['nScans',x] = data_array
            SpinCore_pp.stopBoard();
        data.set_prop('afg_frq', frq_kHz)
        data.name('afg_%d'%frq)    
        nodename = data.name()
        if os.path.exists(output):
            print("this file already exists so we will add a node to it!")
            with h5py.File(
                    os.path.normpath(os.path.join(target_directory,output))
                    ) as fp:
                if nodename in fp.keys():
                    print("this nodename already exists, so I will call it temp_%d"%j)
                    data.name("temp_%d"%j)
                    nodename = "temp_%d"%j
            data.hdf5_write(output,directory = target_directory)
        else:
            try:
                data.hdf5_write(output,directory = target_directory)
            except:
                print(
                        f"I had problems writing to the correct file {output}, so I'm going to try to save your file to temp.h5 in the current directory"
                        ) 
                if os.path.exists("temp.h5"):
                    print("there is a temp.h5 already! -- I'm removing it")
                    os.remove("temp.h5")
                    data.hdf5_write("temp.h5")
                    print(
                        "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
                    )
# }}}
logger.info("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
logger.debug(strm("Name of saved data", output+".h5"))

