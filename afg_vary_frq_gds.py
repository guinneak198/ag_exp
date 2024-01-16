from Instruments import *
from pyspecdata import *
import time
import datetime
from serial.tools.list_ports import comports
import serial
from pylab import *
from timeit import default_timer as timer
from scipy import signal
print("These are the instruments available:")
SerialInstrument(None)
print("done printing available instruments")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
with SerialInstrument('AFG-2225') as s:
    print((s.respond('*idn?')))
#{{{ AFG settings
freq_list = np.linspace(5e6,24e6,50)
amplitude = 0.01 #desired Vpp
output = '240115'+'_'+'GDS_noTL_AFG_10mV_a.h5'
captures = linspace(1,100,75)
with AFG() as a:
    a.reset()
    a[0].ampl = amplitude
    with GDS_scope() as g:
        for j, frq in enumerate(freq_list):
            a[0].output = True
            frq_kHz = frq/1e3 
            print("Frequency is:",frq)
            a.sin(ch=1, V = amplitude, f = frq)
            print("sin wave made")
            time.sleep(30)
            for x in range(1,101):
                ch2_waveform = g.waveform(ch=2)
                data =concat([ch2_waveform],'ch').reorder('t')
                if x ==1:
                    channels = ((ndshape(data)) + ('capture',len(captures))).alloc(dtype = float64)
                    channels.setaxis('t',data.getaxis('t')).set_units('t','s')
                    channels.setaxis('ch',data.getaxis('ch'))
                channels['capture',x-1] = data
                time.sleep(1)
                if not isfinite(data.getaxis('t')[0]):
                    j = 0
                    while not isfinite(data.getaxis('t')[0]):
                        data.setaxis('t',datalist[j].getaxis('t'))
                        j+=1
                        if j == len(datalist):
                            raise ValueError("None of the time axes returned by the scope are finite, which probably means no traces are active??")
            s = channels
            s.labels('capture',captures)
            s.name('afg_%d'%frq_kHz)
            nodename = s.name()
            if os.path.exists(output):
                print("this file already exists so we will add a node to it!")
                with h5py.File(
                        os.path.normpath(os.path.join(target_directory,output))
                        ) as fp:
                    if nodename in fp.keys():
                        print("this nodename already exists, so I will call it temp_%d"%j)
                        s.name("temp_%d"%j)
                        nodename = "temp_%d"%j
                s.hdf5_write(output,directory = target_directory)
            else:
                try:
                    s.hdf5_write(output,directory = target_directory)
                except:
                    print(
                            f"I had problems writing to the correct file {output}, so I'm going to try to save your file to temp.h5 in the current directory"
                            ) 
                    if os.path.exists("temp.h5"):
                        print("there is a temp.h5 already! -- I'm removing it")
                        os.remove("temp.h5")
                        s.hdf5_write("temp.h5")
                        print(
                            "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
                        )
    # }}}
    logger.info("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
    logger.debug(strm("Name of saved data", output+".h5"))


