#!/usr/bin/env python
"""
Created on Mon May 16 2022
@author: Niyaz Beysengulov
"""

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_discrete_set, \
    truncated_discrete_set, truncated_range, strict_range

from time import sleep
import numpy as np

MIN_RAMP_TIME = 0.1  # seconds

""" Functions to communicate with KORAD voltage source"""
    
class KoradKA3305P(Instrument):
    """ Represents the HP8648B signal generator
    and provides a high-level for interacting with the instrument.

    .. code-block:: python

        rf = HP8648B("GPIB::1")

        rf.power_level = -50                # Sets the output power to -50 dBm
        rf.frequency = 156e6                # Sets the frequency of the source to 156 MHz

        rf.enable_source()                  # Enables the output
        rf.disable_source()                 # Enables the output
        rf.ramp_to_power(-120)              # Ramps the power to -120 dBm
        
        rf.shutdown()                     # Ramps the power to -136 dBm and disables output

    """

    voltage_ch1 = Instrument.control(
        "VSET1?", "VSET1:%0.2f",
        """ A floating point property that sets the source power level
        in dBm, which can take values from -136 dBm up to 10 dBm """,
        validator=strict_range,
        values=[0, 30]
    )

    voltage_ch2 = Instrument.control(
        "VSET2?", "VSET2:%0.2f",
        """ A floating point property that sets the source power level
        in dBm, which can take values from -136 dBm up to 10 dBm """,
        validator=strict_range,
        values=[0, 30]
    )

    def __init__(self, resourceName, **kwargs):
        super(KoradKA3305P, self).__init__(
            resourceName,
            "Stanford Research Systems SR844 Lock-in amplifier",
            **kwargs
        )
    
    def enable(self):
        self.write("OUT1")

    def disable(self):
        self.write("OUT0")
        
if __name__=="__main__":
    t = KoradKA3305P('COM3')
    print(t.voltage_ch1)
    print("VSET1:%0.2f" %2.44)
    t.voltage_ch1 = 5.47
    print(t.voltage_ch1)
    t.enable()
    sleep(2)
    t.disable()