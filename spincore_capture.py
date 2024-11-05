from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime
fl = figlist_var()
date = datetime.now().strftime('%y%m%d')
SW_kHz = 200
carrierFreq_MHz = 14.89
output_name = '2toroid_2cable_14p89_a_'+str(SW_kHz)+'kHz'
# {{ Spincore settings
adcOffset = 39
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 100
nPoints = 2048*2

acq_time = nPoints/SW_kHz + 1.0 # ms
tau = 10 + acq_time*1e3*(1./8.)
data_length = 2*nPoints*1*1
for x in range(nScans):
    print(("*** *** *** SCAN NO. %d *** *** ***"%(x+1)))
    print("\n*** *** ***\n")
    print("CONFIGURING TRANSMITTER...")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, 1.0, nPoints)
    print("***")
    print("CONFIGURING RECEIVER...")
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, 1, 1)
    print("***")
    print("\nINITIALIZING PROG BOARD...\n")
    SpinCore_pp.init_ppg();
    SpinCore_pp.load([
        ('marker','start',1),
        ('phase_reset',1),
        ('delay',tau),
        ('acquire',acq_time),
        ('delay',1e4),
        ('jumpto','start')
        ])
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg();
    print("\nRUNNING BOARD...\n")
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, 1, 1).astype(float).view(complex)
    if x == 0:
        time_axis = np.linspace(0.0,acq_time*1e-3,raw_data.size)
        data = ndshape([raw_data.size,nScans],['t','nScans']).alloc(dtype=np.complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:nScans])
        data.name('signal')
    data['nScans',x] = raw_data
    SpinCore_pp.stopBoard();
print("EXITING...")
print("\n*** *** ***\n")
while save_file:
    try:
        print("SAVING FILE...")
        data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type="ODNP_NMR_comp/noise_tests"))
        print("FILE SAVED!")
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("EXCEPTION ERROR - FILE MAY ALREADY EXIST.")
        save_file = False
# {{{ once files are saved correctly, the following become obsolete
fl.next('raw data')
fl.plot(data)
data.ft('t',shift=True)
fl.next('ft')
fl.plot(data.real)
fl.plot(data.imag)
fl.show();quit()
