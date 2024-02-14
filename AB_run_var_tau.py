from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
from SpinCore_pp import prog_plen
fl = figlist_var()
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (nScans < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (p90 < 0.065):
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED PULSE TIME.")
    if (tau < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}

output_name = '27mM_balProbe_varTau_24kHz_p904p4_1scana'
node_name = 'var_tau'
adcOffset = 49
carrierFreq_MHz = 14.89
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1),('ph2',-2)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#{{{ note on timinzag
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 4.4
prog_p90 = prog_plen(p90)
prog_p180 = prog_plen(2*p90)
deadtime = 20.0
repetition = 1e6

SW_kHz = 3.9
acq_ms = 1024
nPoints = int(acq_ms*SW_kHz+0.5)
nPoints = 1024*2

acq_time = nPoints/SW_kHz # ms
tau_adjust_range = r_[1e3:35e3:5e3]#np.linspace(1e1,50e3,30)
print("TAU RANGE:")
print(tau_adjust_range)
input("Does this look okay?")
deblank = 1.0
tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust_range
tau = deadtime + 51.2*1e3*(1./8.) + tau_adjust_range
tau_axis = tau
print("TAU US:",tau)
input("okay?")
pad = 0
#pad = 2.0*tau - deadtime - acq_time*1e3 - deblank
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amplitude
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust_range
acq_params['deblank_us'] = deblank
acq_params['tau_us'] = tau
#acq_params['pad_us'] = pad 
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
print(("ACQUISITION TIME:",acq_time,"ms"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
for index,val in enumerate(tau_adjust_range):
    tau_adjust = val # us
    # calculate tau each time through
    tau = deadtime + acq_time*1e3*(1./8.) + tau_adjust_range[index]
    #tau = tau_adjust
    #tau = deadtime + tau_adjust
    print("***")
    print("INDEX %d - TAU %f"%(index,tau))
    print("***")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    SpinCore_pp.init_ppg();
    for x in range(nScans):
        if phase_cycling:
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                ('delay_TTL',deblank),
                ('pulse_TTL',prog_p90,'ph1',r_[0,1,2,3]),
                ('delay',tau),
                ('delay_TTL',deblank),
                ('pulse_TTL',prog_p180,'ph2',r_[0]),#r_[0,2]),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
        if not phase_cycling: 
            SpinCore_pp.load([
                ('marker','start',nScans),
                ('phase_reset',1),
                ('delay_TTL',deblank),
                ('pulse_TTL',prog_p90,0.0),
                ('delay',tau),
                ('delay_TTL',deblank),
                ('pulse_TTL',prog_p180_us,0.0),
                ('delay',deadtime),
                ('acquire',acq_time),
                ('delay',repetition),
                ('jumpto','start')
                ])
        SpinCore_pp.stop_ppg();
        #if phase_cycling:
        #    for x in range(nScans):
        #        print("SCAN NO. %d"%(x+1))
        SpinCore_pp.runBoard();
        if not phase_cycling:
            SpinCore_pp.runBoard();
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps)
        raw_data.astype(float)
        data = []
        # according to JF, this commented out line
        # should work same as line below and be more effic
        #data = raw_data.view(complex128)
        data[::] = np.complex128(raw_data[0::2]+1j*raw_data[1::2])
        print("COMPLEX DATA ARRAY LENGTH:",np.shape(data)[0])
        print("RAW DATA ARRAY LENGTH:",np.shape(raw_data)[0])
        dataPoints = float(np.shape(data)[0])
        time_axis = np.linspace(int(0),nEchoes*nPhaseSteps*acq_time*1e-3,int(dataPoints))
        data = nddata(np.array(data),'t')
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        if index == 0 and x == 0:
            var_tau_data = ndshape([len(tau_adjust_range),nScans,len(time_axis)],['tau','nScans','t']).alloc(dtype=np.complex128)
            var_tau_data.setaxis('tau',tau_axis*1e-6).set_units('tau','s')
            var_tau_data.setaxis('nScans',r_[0:nScans])
            var_tau_data.setaxis('t',time_axis).set_units('t','s')
        var_tau_data['tau',index]['nScans',x] = data
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        var_tau_data.set_prop('acq_params',acq_params)
        var_tau_data.name('var_tau')
        var_tau_data.name(node_name)
        var_tau_data.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",var_tau_data.name())
        print("Units of saved data",var_tau_data.get_units('t'))
        print("Shape of saved data",ndshape(var_tau_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            var_tau_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
fl.image(var_tau_data)
var_tau_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(var_tau_data)
fl.show()

