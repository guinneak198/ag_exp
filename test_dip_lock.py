"""the idea here is that we are going to plot out the
frequency sweep result that leads to the error when we
are trying to lock on the dip, to see what is causing
the issue.  Based on the error, it could be that we are
in the wrong frequency range altogether, but it could
also be that we are taking such coarse steps that we
are skipping over the dip -- this is why I plot  with
the `o-` style, to explicitly show the samples that we
are taking.  I would recommend that after plotting with
this to see what it looks like, you can try changing
the range (and maybe your power) in order to see your dip.
?
For example, start by printing ini_range and ini_step
right before the call to self.freq_sweep
inside the lock_on_dip function inside the bridge12.py
module.
"""
from Instruments import Bridge12
from pyspecdata import *
ini_range = (9.817e9,9.822e9)# print out what this is set to when you get the error
ini_step = 0.2e6# print out what this is set to when you get the error
with Bridge12() as b:
    b.set_wg(True)
    b.set_amp(True)
    b.set_rf(True)
    b.set_power(10.0)
    freq = r_[ini_range[0] : ini_range[1] : ini_step]
    rx, tx = b.freq_sweep(freq)
plot(freq, rx, 'o-', label="reflection profile")
show()
