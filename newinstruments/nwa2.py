# -*- coding: utf-8 -*-
"""
-- Camille Mikolas --
Created January 2024

Extension of and built upon from Dave Schuster Lab code see: https://github.com/SchusterLab/slab/blob/master/slab/instruments/nwa.py

Many commands come from following SCPI programming manual: https://mcs-testequipment.com/content/files/Ceyear-3656-Series-Programming-Manual.pdf

"""
from .instrumenttypes import SocketInstrument, VisaInstrument, SerialInstrument
import time, glob, re
import numpy as np
import os.path
from matplotlib import pyplot as plt


class E5071_2(VisaInstrument):
    MAXSWEEPPTS = 1601
    default_port = 5025

    def __init__(self, name = 'E5071', address = 'GPIB0::2::INSTR', enabled=True, timeout=None):

        VisaInstrument.__init__(self, name, address, enabled, timeout=2e5)
        self.query_sleep = 0.1

    def get_id(self):
        #Identification query that will tell you about the device it is connected to
        return self.query('*IDN?')
    
    def get_query_sleep(self):
        #Returns the query sleep time set in Visa initialization 
        return self.query_sleep
    
    def set_display_state(self, state=True):
        #Turns on or off the display on VNA
        enable = 'ON' if state else 'OFF'
        self.write('DISP:ENAB %s' % enable)

    def get_display_state(self):
        return self.query('DISP:ENAB?')
    

    # Frequency setup


    def set_start_frequency(self, freq, channel=1):
        self.write(":SENS%d:FREQ:START %f" % (channel, freq))

    def get_start_frequency(self, channel=1):
        return float(self.query(":SENS%d:FREQ:START?" % channel))

    def set_stop_frequency(self, freq, channel=1):
        self.write(":SENS%d:FREQ:STOP %f" % (channel, freq))

    def get_stop_frequency(self, channel=1):
        return float(self.query(":SENS%d:FREQ:STOP?" % channel))

    def set_center_frequency(self, freq, channel=1):
        self.write(":SENS%d:FREQ:CENTer %f" % (channel, freq))

    def get_center_frequency(self, channel=1):
        return float(self.query(":SENS%d:FREQ:CENTer?" % channel))

    def set_span(self, span, channel=1):
        return self.write(":SENS%d:FREQ:SPAN %f" % (channel, span))

    def get_span(self, channel=1):
        return float(self.query(":SENS%d:FREQ:SPAN?" % channel))


    # Averaging setup

    def get_operation_completion(self):
        # Queries instrument if all operations in block is completed before it can move on to next block
        data = self.query("*OPC?")
        if data is None:
            return False
        else:
            return bool(int(data.strip()))
        
    def set_averages(self, averages, channel=1):
        self.write(":SENS%d:AVERage:COUNt %d" % (channel, averages))

    def get_averages(self, channel=1):
        return int(self.query(":SENS%d:average:count?" % channel))
    
    def set_average_state(self, state, channel=1):
        if state==True or state=='ON':
            s = "ON"
        else:
            s = "OFF"
        self.write(":SENS%d:AVERage:state %s" % (channel, s))

    def get_average_state(self, channel=1):
        st = self.query(":SENS%d:AVER:STATE?" % channel).strip()
        if st == '1':
            ans = True
        else:
            ans = False
        return ans

    def clear_averages(self, channel=1):
        self.write(":SENS%d:average:clear" % channel)

    def set_ifbw(self, bw, channel=1):
        self.write(":SENS%d:BANDwidth:RESolution %f" % (channel, bw))

    def get_ifbw(self, channel=1):
        return float(self.query(":SENS%d:BANDwidth:RESolution?" % (channel)))

    def averaging_complete(self):
        self.write("*OPC?")
        self.read()

    def avg_comp_ask(self):
        answ = self.write("*OPC?")
        return answ

    # Trigger settings
        
    def trigger_single(self, channel):
        """
        Send a single trigger to all channels.
        :return: None
        """
        if channel == None:
            self.write(':TRIG:SCOP ALL')
            self.write(':INIT:IMM')
        else:
            self.write(':INIT%d:IMM' % channel)

    def set_trig_sweep_mode(self, mode, channel):
        self.write("SENS%d:SWE:MODE %s" % (channel, mode))

    def get_trig_sweep_mode(self, channel):
        return (self.query("SENS%d:SWE:MODE?" % channel)).strip()

    def set_trigger_average_mode(self, state=True):
        """
        If state=True, the machine initiates averaging when it receives a single trigger. It keeps
        averaging until the averaging is complete.
        :param state: bool
        :return: None
        """
        if state:
            self.write(':TRIG:AVER ON')
        else:
            self.write(':TRIG:AVER OFF')

    def get_trigger_average_mode(self):
        """
        Returns the trigger averaging mode. If True, the machine operates in a way where it keeps averaging
        a trace until averaging is complete, with only a SINGLE trigger necessary.
        :return: bool
        """
        return bool(self.query(':TRIG:AVER?'))

    def set_trigger_source(self, source):
        """
        Sets the trigger source to one of the following:
        IMMediate (internal source sends continuous trig signals), 
        MANual (sends one trig signal when manually triggered), 
        EXTernal (external rear panel source)
        :param source: string
        :return: None
        """
        self.write(':TRIG:SEQ:SOUR %s' % source)

    def get_trigger_source(self):
        """
        Returns the trigger source.
        :return: string
        """
        answer = self.query(':TRIG:SEQ:SOUR?')
        return answer.strip()

    def set_trigger_continuous(self, state):
        """
        Set the trigger mode to continuous (if state = True) or set the state to Hold (if state = False)
        :param state: bool
        :return: None
        """
        if state == True or state == "ON":
            set = "ON"
        elif state ==False or state == "OFF":
            set = "OFF"
        self.write(':INIT:CONT %s' % set)

    def get_trigger_continuous(self):
        """
        Returns True if the trigger mode is set to Continuous, or False if the trigger mode is set to Hold.
        :return: bool
        """
        state = (self.query(':INIT:CONT?')).strip()
        if state=='0':
            state = False
        elif state == '1':
            state = True
        return state

    def set_trigger_in_polarity(self, polarity=1):
        """
        Set the external input trigger polarity. If polarity = 1, the external trigger is set to the positive edge,
        if polarity = 0, the machine triggers on the negative edge.
        :param polarity:
        :return: None
        """
        set = 'POS' if polarity else 'NEG'
        self.write(':TRIG:SEQ:EXT:SLOP %s' % set)

    def get_trigger_in_polarity(self):
        """
        Returns the trigger slope for the external trigger. Returns 1 for triggering on positive edge, or
        0 for triggering on the negative edge.
        :return: integer
        """
        answer = self.query(':TRIG:SEQ:EXT:SLOP?')
        ret = 1 if answer.strip() == 'POS' else 0
        return ret

    def set_trigger_low_latency(self, state=True):
        """
        This command turns ON/OFF or returns the status of the low-latency external trigger feature.
        When turning on the low-latency external trigger feature, the point trigger feature must be set
        to on and the trigger source must be set to external trigger.
        :param state: bool
        :return: None
        """
        set = 'ON' if state else 'OFF'
        self.write(':TRIG:EXT:LLAT %s'%set)

    def get_trigger_low_latency(self):
        """
        Returns the low latency external trigger status
        :return: bool
        """
        answer = self.query(':TRIG:EXT:LLAT?')
        return bool(answer.strip())

    def set_trigger_event(self, state, channel):
        """
        This command turns ON/OFF the status of the point trigger feature.
        If ON, channel measures one point per trigger, if OFF measures all in channel per trigger
        :param state: string ('sweep' or 'point')
        :return: None
        """
        if state == "ON" or state == True:
            self.write('SENS%d:SWE:TRIG:POIN ON' % channel)
        else:
            self.write('SENS%d:SWE:TRIG:POIN OFF' % channel)

    def get_trigger_event(self, channel):
        """
        This command returns the status of the point trigger feature.
        :param state: string ('sweep' or 'point')
        :return: bool
        """
        answer = self.query('SENS%d:SWE:TRIG:POIN?' % channel)
        return bool(answer.strip())

    def set_trigger_out_polarity(self, polarity=1):
        """
        Sets the external output trigger polarity. If polarity = 1, the external trigger is a positive voltage
        pulse. If polarity = 0, the external trigger is a negative voltage pulse.
        :param polarity: integer
        :return: None
        """
        set = 'POS' if polarity else 'NEG'
        self.write('TRIG:OUTP:POL %s' % set)


    # Source/Measurement settings
        
    def set_power(self, power, channel=1):
        self.write(":SOURCE%d:POWER %f" % (channel, power))

    def get_power(self, channel=1):
        return float(self.query(":SOURCE%d:POWER?" % channel))

    def set_output(self, state=True):
        if state==True or str(state).upper() == 'ON':
            self.write(":OUTPUT ON")
        elif state == False or str(state).upper() == 'OFF':
            self.write(":OUTPUT OFF")

    def get_output(self):
        output = self.query(":OUTPUT?")
        if output == '1\n':
            return True
        elif output == '0\n':
            return False
        
    def set_measure_def(self, measure_name, mode, channel):
        """ sets up definition of measurement type 
        with any name of choosing
        """
        self.write(':CALC%d:PAR:DEF %s, %s' % (channel, measure_name, mode))

    def set_measure(self, measure_name, channel):
        #set measurement based on defined name
        self.write('CALC%d:PAR:SEL %s' % (channel, measure_name))

    def get_current_measure(self, channel):
        if channel==None:
            ch = 1
            answer = self.query('CALC%d:PAR:SEL?' % (ch))
        else:
            answer = self.query('CALC%d:PAR:SEL?' % (channel))
        return answer
    
    def get_measure_defs(self, channel):
        # lists saved measurement definitions
        
        if channel==None:
            return str(self.query(':CALC1:PAR:CAT?'))
        else:
            return str(self.query(':CALC%d:PAR:CAT?' % channel))
  
    def delete_measure_defs(self, measure_name, channel = 1):
        # deletes specified or ALL measurement definitions
        if measure_name == 'ALL':
            self.write('CALC:PAR:DEL:ALL')
        else:
            self.write(':CALC%d:PAR:DEL %s' % (channel,measure_name))

    def create_meas_in_window(self, channel, measure_name):
        #creating window for measurement
        #self.write('DISP:WIND%d:STATE ON' % channel)

        #putting measurement setup in window
        self.write('DISP:WIND%d:TRAC%d:FEED %s' % (channel, channel, measure_name))

    def close_window(self, channel):
        self.write('DISP:WIND%d:STATE OFF' % channel)

    def hold_meas(self, channel):
        # holds the VNA from measurement
        if channel==None:
            ch = 1
            self.write("SYST:CHAN%d:HOLD" % ch)
        else:
            self.write("SYST:CHAN%d:HOLD" % channel)
    
    def resume_meas(self, channel):
        """ resumes trigger mode of all channels 
        that was in effect before sending the hold
        """
        if channel==None:
            self.write("SYST:CHAN1:RES")
        else:
            self.write("SYST:CHAN%d:RES" % channel)
  
    
    # Sweep stuff 
            

    def get_sweep_time(self, channel=1):
        """
        Returns the sweep time in seconds.
        :param channel: channel number
        :return: float
        """
        answer = self.query(":SENS%d:SWE:TIME?"%channel)
        return float(answer.strip())

    def set_sweep_time(self, sweep_time, channel=1):
        """
        Sets the sweep time in seconds. If the sweep time is set to 'AUTO', this function first sets the sweep time
        to manual. Then it sets the sweep time to "sweep_time". This value cannot be lower than the value when the
        sweep time is set to auto.
        :param sweep_time: sweep time in seconds
        :param channel: channel number
        :return: None
        """
        self.set_sweep_time_auto(state=False, channel=channel)
        self.write(":SENS%d:SWE:TIME %.3e"%(channel, sweep_time))

    def set_sweep_time_auto(self, state=True, channel=1):
        """
        Sets the sweep time to automatic (the fastest option).
        :param state: True/False
        :param channel: channel number
        :return: None
        """
        set = 'ON' if state==True else 'OFF'
        self.write(":SENS%d:SWE:TIME:AUTO %s" % (channel, set))

    def get_sweep_time_auto(self, channel=1):
        """
        Returns True if the sweep time is automatically set, or False if the sweep time is set manually.
        :param channel: channel number
        :return: bool
        """
        answer = self.query(":SENS%d:SWE:TIME:AUTO?" % channel)
        return bool(answer.strip())

    def set_sweep_points(self, numpts=1600, channel=1):
        """
        Sets the number of sweep points
        :param numpts: integer
        :param channel: channel number
        :return: None
        """
        self.write(":SENSe%d:SWEep:POINts %f" % (channel, numpts))

    def get_sweep_points(self, channel=1):
        """
        Returns the number of points in the current sweep.
        :param channel: channel number
        :return: integer
        """
        return int(self.query(":SENSe%d:SWEep:POINts?" % (channel)))

    def set_sweep_type(self, sweep_type, channel=1):
        """
        :param sweep_type: one of the following: ["LIN", "LOG", "SEGM", "POW"]. Default: "LIN"
        :param channel: channel number
        :return: None
        """
        if sweep_type.upper() in ["LIN", "LOG", "SEGM", "POW"]:
            self.write("SENS%d:SWE:TYPE %s" % (channel, sweep_type.upper()))
        else:
            print("sweep_type must be one of LIN (linear frequency), LOG (logarithmic frequency), SEGM (segmented sweep) or POW (power sweep)")

    def get_sweep_type(self, channel=1):
        answer = self.query("SENS%d:SWE:TYPE?" % (channel))
        return answer.strip()

    def set_sweep_generation(self, channel, generation):
        self.write("SENS%d:SWE:GEN %s" % (channel, generation))

    def get_sweep_generation(self, channel):
        return (self.query("SENS%d:SWE:GEN?" % channel)).strip()
    

    # Scale 
    def get_phase_offset(self, channel=1):
        """
        This command gets the phase offset of the active trace of selected channel
        :return: float
        """
        #answer = self.query(":CALC%d:CORR:OFFS:PHAS?" % (channel))
        #return float(answer.strip())
        return print("Haven't figured this one out yet, sorry!")

    def set_phase_offset(self, offset, channel=1):
        """
        This command sets the phase offset of the active trace of selected channel
        :param offset: offset in degrees
        :param channel: integer
        :return: None
        """
        #self.write(":CALC%d:CORR:OFFS:PHAS %.4f" % (channel, offset))
        return print("Haven't figured this one out yet, sorry!")

    def get_electrical_delay_info(self, channel):
        """
        Returns the electrical delay in seconds -- useful when wanting to compensate for phase data shifting from lossy delay line
        :param channel: channel number
        :return: float
        """
        #self.set_measure(measure_name, channel)
        medium = self.query(':CALC%d:CORR:EDEL:MED?' % channel).strip()
        answer = self.query(":CALC%d:CORR:EDEL:TIME?" % (channel))
        print('Electrical delay medium is ' + medium + ' and electrical delay time is ' + answer)
    
    def get_electrical_delay_time(self, channel):
        """
        Returns the electrical delay in seconds -- useful when wanting to compensate for phase data shifting from lossy delay line
        :param channel: channel number
        :return: float
        """
        answer = self.query(":CALC%d:CORR:EDEL:TIME?" % (channel))
        return float(answer)

    def set_electrical_delay(self, electrical_delay, channel=1):
        """
        Sets the electrical delay of the trace. The number should be between -10s and 10s.
        :param electrical_delay: float
        :param channel: channel number
        :return: None
        """
        self.write(":CALC%d:CORR:EDEL:TIME %.6e"%(channel, np.float64(electrical_delay)))

    def auto_scale(self, channel=1, trace_number=1):
        """
        Auto-scales the y-axis of the trace with trace_number.
        :param channel: channel number
        :param trace_number: integer
        :return: None
        """
        self.write(":DISP:WIND%d:TRAC%d:Y:AUTO"%(channel, trace_number))

    def set_scale(self, scale_value):
        self.write('DISP:WIND:TRAC:Y:PDIV %.6e' % (scale_value))

    def get_scale(self, channel=1):
        answ = self.query('DISP:WIND%d:TRAC%d:Y:SCAL:PDIV?' % (channel,channel))
        return float(answ)
    
    def set_full_measure(self, measure_name = 'MeaS12', measure_type = 'S12', channel=1):
        self.delete_measure_defs('ALL')
        self.set_measure_def(measure_name, measure_type, channel)
        self.create_meas_in_window(channel, measure_name)

    
    # File operations
        
    def save_file(self, fname):
        self.write('MMEMORY:STORE:FDATA \"' + fname + '\"')

    def set_format(self, trace_format, channel=1):
        """
        set_format: valid options are
        {MLOGarithmic|PHASe|GDELay| SLINear|SLOGarithmic|SCOMplex|SMITh|SADMittance|PLINear|PLOGarithmic|POLar|MLINear|SWR|REAL| IMAGinary|UPHase|PPHase}
        """
        self.write(":CALC%d:FORM %s" % (channel, trace_format))

    def get_format(self, channel=1):
        """
        get_format: valid options are
        {MLOGarithmic|PHASe|GDELay| SLINear|SLOGarithmic|SCOMplex|SMITh|SADMittance|PLINear|PLOGarithmic|POLar|MLINear|SWR|REAL| IMAGinary|UPHase|PPHase}
        """
        return self.query(":CALC%d:FORM?" % channel)

    def get_fpoints(self, channel=1):
        """
        This command gives the frequency points of current configuration
        https://mcs-testequipment.com/content/files/Ceyear-3656-Series-Programming-Manual.pdf motherfuvkre
        """
        answer = self.query('SENS:X?')
        return np.fromstring(answer, dtype=np.float64, sep=',')

    def read_data(self, channel=1, timeout=None, sweep_type=None):
        """
        Read current NWA Data, output depends on format, for mag phase, use set_format('SLOG')
        :param channel: channel number
        :param timeout: optional, query timeout in ms.
        :return: np.vstack((fpts, data))
        """
        #self.get_operation_completion()
        measure_def = self.get_measure_defs(channel).strip()
        currmeas = self.get_current_measure(channel).strip()
        if measure_def != '"NO CATALOG"' and  currmeas != '""':
            self.write(":FORM:DATA ASC") # sets to ASCii formatting
            self.write(":CALC%d:DATA? FDATA" % channel)
            time.sleep(self.query_sleep)

            if timeout is None:
                timeout = self.timeout

            data_temp = self.read(timeout=timeout)
            data_str = ''.join([ss for ss in data_temp])
            data = np.fromstring(data_str, dtype=float, sep=',')
            sweep_points = int(self.get_sweep_points())
            sweep_type = self.get_sweep_type(channel=channel) if sweep_type is None else sweep_type

            fpts = self.get_fpoints()
            # print(len(fpts), len(data))

            if len(data) == 2 * sweep_points:
                data = data.reshape((-1, 2))
                data = data.transpose()
                return np.vstack((fpts, data))
            else:
                return np.vstack((fpts, data))
        else:
            print('no measure definition')

    def read_data_y1(self):
        """
        Read current NWA Data, output depends on format, for mag phase, use set_format('SLOG')
        :param channel: channel number
        :param timeout: optional, query timeout in ms.
        :return: np.vstack((fpts, data))
        """
        dat = self.read_data()
        return dat[1,:]
    
    def read_data_y2(self):
        form = self.get_format().strip()
        print(form)
        if form in ['SMIT', 'POL', 'SADM']:
            dat = self.read_data()
            return dat[2,:]
        else:
            print('Not a valid format for this function')
            return None
            
        
    def take_one_averaged_trace(self, fname=None):
        """Setup Network Analyzer to take a single averaged trace and grab data, either saving it to fname or returning it"""
        print("Acquiring single trace")
        self.set_trigger_source('CONTINUOUS') #Need to change back to BUS
        time.sleep(self.query_sleep * 2)
        old_timeout = self.get_timeout()
        # self.set_timeout(100.)
        self.set_format()
        time.sleep(self.query_sleep)
        old_avg_mode = self.get_trigger_average_mode()
        self.set_trigger_average_mode(True)
        self.clear_averages()
        self.trigger_single()
        time.sleep(self.query_sleep)
        self.averaging_complete()  # Blocks!
        self.set_format('SLOG ')
        if fname is not None:
            self.save_file(fname)
        ans = self.read_data()
        time.sleep(self.query_sleep)
        self.set_timeout(old_timeout)
        self.set_trigger_average_mode(old_avg_mode)
        self.set_trigger_source('CONTINUOUS') #change back to internal
        self.set_format()
        return ans