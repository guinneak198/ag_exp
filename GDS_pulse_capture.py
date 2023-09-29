"""Zoom out to about 10 us timescale on GDS, and 100 mV. Acquire mode should be Hi resolution and trigger should be set to normal
"""
from pyspecdata import *
import os
from Instruments import *
import SpinCore_pp
from SpinCore_pp import prog_plen
import socket
import sys
import time
from datetime import datetime
import numpy as np
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
#{{{ for setting EPR magnet
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv) > 1:
        IP = sys.argv[1]
    PORT = 6001
    print("target IP:", IP)
    print("target port:", PORT)
    MESSAGE = str(value)
    print("SETTING FIELD TO...", MESSAGE)
    sock = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_STREAM) # TCP
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print("FIELD SET TO...", MESSAGE)
    time.sleep(5)
    return
#}}}
date = datetime.now().strftime('%y%m%d')
output_name = '100tau_p90_3p75_GDS'
adcOffset = 48
carrierFreq_MHz = 14.893504
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 1
nEchoes = 1
nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
GDS = True
deadtime = 10.0
repetition = 0.25e6
SW_kHz = 3.9#50.0
nPoints = 2048#int(aq/SW_kHz+0.5)#1024*2
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = 100#5e3#deadtime + acq_time*1e3*(1./8.) + tau_adjust
p90 = 3.75#us (28x expected 90 time)
prog_p90_us = prog_plen(p90)
prog_p180_us = prog_plen(2*p90)
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
data_length = 2*nPoints*nEchoes*nPhaseSteps
amp_range = np.linspace(0,0.5,200)[1:]#,endpoint=False)
#{{{ setting acq_params dictizaonary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amp_range
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = 1.0
acq_params['tau_us'] = tau
#acq_params['pad_us'] = pad 
#}}}
amp_list = [1.0,1.0,1.0,1.0,1.0]
for index,val in enumerate(amp_list):
    #p90 = val # us
    amplitude = 1.0 # pulse amp, set from 0.0 to 1.0
    print("***")
    print("INDEX %d - AMPLITUDE %f"%(index,val))
    print("***")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    SpinCore_pp.init_ppg();
    SpinCore_pp.load([
        ('marker','thisstart',1),
        ('phase_reset',1),
        ('delay_TTL',1.0),
        ('pulse_TTL',prog_p90_us,0),
        ('delay',tau),
        ('delay_TTL',1.0),
        ('pulse_TTL',prog_p180_us,0),
        ('delay',deadtime),
        ('acquire',acq_time),
        ('delay',repetition),
        ('jumpto','thisstart'),
        ])
    SpinCore_pp.stop_ppg();
    SpinCore_pp.runBoard();
    #raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    #raw_data.astype(float)
    datalist = []
    datalist1 = []
    with GDS_scope() as g:
        print("ACQUIRING")
        #g.acquire_mode('average',8)
        print("ACQUIRED")
        for j in range(1,len(amp_list)+1):
            print("TRYING TO GRAB WAVEFORM")
            datalist.append(g.waveform(ch=2))
        print("GOT WAVEFORM")
        nutation_data = concat(datalist,'ch').reorder('t')
    SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
s = nutation_data['ch',0]
s.set_units('t','s')
fl.next('sequence')
fl.plot(s)


save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        nutation_data.set_prop('acq_params',acq_params)
        nutation_data.name('GDS_capture')
        nutation_data.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",nutation_data.name())
        print("Units of saved data",nutation_data.get_units('t2'))
        print("Shape of saved data",ndshape(nutation_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            nutation_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.show()


