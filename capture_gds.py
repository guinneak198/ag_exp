"""
Capture the signal acquired on the GDS. and converts to analytic 
================================================================
A single capture of the signal on the GDS is converted to analytic signal,
frequency filtered and the absolute is taken to calculate the :math:`V_{amp}`
the voltage ratio and the dB of the setup based on the voltage ratio.
"""
from Instruments import GDS_scope
from pyspecdata import figlist_var
from pylab import axhline, text, gca

expected_Vamp = 500e-3  # what is expected on the GDS
assert expected_Vamp < 505e-3, (
    "That's way too high of a peak voltage! You either need an attenuator or"
    " you didn't put the input in units of V"
)
with figlist_var() as fl:
    with GDS_scope() as g:
        g.reset()
        # {{{ display settings
        g.CH1.disp = True
        g.CH2.disp = True
        g.write(":CHAN1:DISP OFF")
        g.write(":CHAN2:DISP ON")
        g.write(":CHAN3:DISP OFF")
        g.write(":CHAN4:DISP OFF")
        # }}}
        # {{{ voltage scale and acquisition settings
        g.CH2.voltscal = (
            expected_Vamp * 1.1 / 4
        )  # set to a little more than $\frac{V_{amp}}{4}$
        g.timscal(10e-9, pos=0)
        g.write(":TIM:MOD WIND")
        g.write(":CHAN2:IMP 5.0E+1")  # set impedance to 50 ohms
        g.write(":TRIG:SOUR CH2")  # set the source of the trigger to channel 2
        g.write(":TRIG:MOD AUTO")  # set trigger to auto
        g.write(":ACQ:MOD HIR")  # high vertical res.
        # }}}
        # {{{ set horizontal cursors on oscilloscope display
        g.write(":CURS:MOD HV")  # set cursors
        g.write(":CURS:SOUR CH2")  # cursors pertain to channel 2
        # }}}
        # {{{ use expected amplitude to set initial
        #     position of cursors
        mycursors = (expected_Vamp, -expected_Vamp)
        g.write(":CURS:V1P " + ("%0.2e" % mycursors[0]).replace("e", "E"))
        g.write(":CURS:V2P " + ("%0.2e" % mycursors[1]).replace("e", "E"))
        # }}}
        # {{{ grab waveform from oscilloscope
        g.write(":SING")  # capture single acquisition
        data = g.waveform(ch=2)
        data.set_units("t", "s")
        # }}}
    fl.next("data")
    fl.plot(data, label="original signal")
    # {{{ convert to analytic signal
    data.ft("t", shift=True)
    data = data["t":(0, None)]
    data *= 2
    data["t", 0] *= 0.5
    data.ift("t")
    # }}}
    # {{{ show the manual cursor positions
    for y in mycursors:
        axhline(y=y, color="k", alpha=0.5)
    # }}}
    fl.plot(abs(data), label="abs(analytic signal)")
    # calculate average frequency of signal
    frq = data.C.phdiff("t", return_error=False).mean("t").item()
    # {{{ now, filter the signal
    data.ft("t")
    data["t" : (0, frq - 5e6)] = 0
    data["t" : (frq + 5e6, None)] = 0
    data.ift("t")
    # }}}
    fl.plot(data, label="filtered analytic signal")
    fl.plot(abs(data), label="abs(filtered analytic signal)")
    # don't include first μs since on occasion there is a spike
    # that doesn't fall in line with the rest of the signal
    Vamp = abs(data["t":(1e-6, None)]).mean("t").real.item()
    text(
        0.5,
        0.9,
        s=r"$V_{amp} = %#0.7g\;\mathrm{mV}$" % (Vamp / 1e-3),
        transform=gca().transAxes,
    )
