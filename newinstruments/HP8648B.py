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

""" Functions to communicate with HP8648B signal generator"""
    
class HP8648B(Instrument):
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

    power_level = Instrument.control(
        "POW:AMPL?", ":POW:LEV:AMPL %0.3f"+"DBM",
        """ A floating point property that sets the source power level
        in dBm, which can take values from -136 dBm up to 10 dBm """,
        validator=strict_range,
        values=[-136, 13.5]
    )

    frequency = Instrument.control(
        "FREQ:CW?", ":SOUR:FREQ:CW %0.3f",
        """ A floating point property that sets the source frequency
        in Hz, which can take values from 9 kHz up to 2 GHz """,
        validator=strict_range,
        values=[9e3, 2e9]
    )

    @property
    def voltage_level(self):
        measured_power = self.power_level
        return np.sqrt(5)*10**(measured_power/20 - 1)

    @voltage_level.setter
    def voltage_level(self, voltage):
        set_power = 20*np.log10(voltage/np.sqrt(0.001*50))
        self.power_level = set_power

    def ramp_to_power(self, power, duration=0.5):
        """ Ramps the voltage to a value in Volts by traversing a linear spacing
        of voltage steps over a duration, defined in seconds.

        :param steps: A number of linear steps to traverse
        :param duration: A time in seconds over which to ramp
        """
        steps = 25
        start_power = self.power_level
        stop_power = power
        pause = duration/steps
        if (start_power != stop_power):
            powers = np.linspace(start_power, stop_power, steps)
            for power in powers:
                self.power_level = power
                sleep(pause)
    
    def ramp_to_voltage(self, voltage, duration=0.5):
        """ Ramps the voltage to a value in Volts by traversing a linear spacing
        of voltage steps over a duration, defined in seconds.

        :param steps: A number of linear steps to traverse
        :param duration: A time in seconds over which to ramp
        """
        steps = 25
        start_voltage = self.voltage_level
        stop_voltage = voltage
        pause = duration/steps
        if (start_voltage != stop_voltage):
            voltages = np.linspace(start_voltage, stop_voltage, steps)
            for voltage in voltages:
                self.voltage_level = voltage
                sleep(pause)

    def ramp_to_freq(self, frequency, duration=0.5):
        """ 
        """
        self.frequency = frequency
        sleep(duration)

    def enable(self):
        self.write(":OUTP:STAT ON")

    def disable(self):
        self.write(":OUTP:STAT OFF")

    def __init__(self, adapter, **kwargs):
        super(HP8648B, self).__init__(
            adapter, "HP8648B signal generator", **kwargs
        )

if __name__=="__main__":
    t = HP8648B('GPIB0::20::INSTR')
    t.voltage_level = 0.01
    print(t.voltage_level)
    print(t.power_level)
    t.enable()