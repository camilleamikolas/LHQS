"""
Created:                    Niyaz Beysengulov 

File:                       a_in_scan_foreground.py

Library Call Demonstrated:  mcculw.ul.a_in_scan() in Foreground mode

Purpose:                    Scans a range of A/D Input Channels and stores
                            the sample data in an array.

Demonstration:              Displays the analog input on up to four channels.

Other Library Calls:        mcculw.ul.win_buf_alloc()
                                or mcculw.ul.win_buf_alloc_32
                                or mcculw.ul.scaled_win_buf_alloc()
                            mcculw.ul.win_buf_free()
                            mcculw.ul.to_eng_units()
                            mcculw.ul.release_daq_device()

Special Requirements:       Device must have an A/D converter.
                            Analog signals on up to four input channels.
"""

from __future__ import absolute_import, division, print_function
from builtins import *  # @UnusedWildImport

from ctypes import cast, POINTER, addressof, sizeof, c_double, c_ushort, c_ulong
from time import sleep

from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status, TrigType, ULRange
from mcculw.device_info import DaqDeviceInfo

import numpy as np

class mcc_daq:
    
    def __init__(self, sampling_rate = 100, measurement_time = 1, voltage_range = 0, status = True):
        self.sampling_rate = int(sampling_rate)
        self.measurement_time = measurement_time
        self.voltage_range = voltage_range     # 0 - 10 VOLTS, 1 - 2.5 VOLTS, 2 - 0.5 VOLTS
        self.status = status
    
    def device_detect(self):
        try:
            from mcc_console_examples_util import config_first_detected_device
        except ImportError:
            from .mcc_console_examples_util import config_first_detected_device
        
        self.use_device_detection = True
        dev_id_list = []
        self.board_num = 0
        
        if self.use_device_detection:
            config_first_detected_device(self.board_num, dev_id_list)

        self.daq_dev_info = DaqDeviceInfo(self.board_num)
        if not self.daq_dev_info.supports_analog_input:
            raise Exception('Error: The DAQ device does not support '
                            'analog input')

        print('\nActive DAQ device: ', self.daq_dev_info.product_name, ' (',
              self.daq_dev_info.unique_id, ')\n', sep='')
    
    def scan(self):
        points_per_channel = int(self.measurement_time * self.sampling_rate)
        memhandle = None
        ai_info = self.daq_dev_info.get_ai_info()
        low_chan = 0
        high_chan = min(3, ai_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1
        total_count = points_per_channel * num_chans

        ai_range = ai_info.supported_ranges[self.voltage_range]
        scan_options = ScanOptions.FOREGROUND
        
        if ScanOptions.SCALEDATA in ai_info.supported_scan_options:
            # If the hardware supports the SCALEDATA option, it is easiest to
            # use it.
            scan_options |= ScanOptions.SCALEDATA

            memhandle = ul.scaled_win_buf_alloc(total_count)
            # Convert the memhandle to a ctypes array.
            # Use the memhandle_as_ctypes_array_scaled method for scaled
            # buffers.
            ctypes_array = cast(memhandle, POINTER(c_double))
        elif ai_info.resolution <= 16:
             # Use the win_buf_alloc method for devices with a resolution <= 16
            memhandle = ul.win_buf_alloc(total_count)
            # Convert the memhandle to a ctypes array.
            # Use the memhandle_as_ctypes_array method for devices with a
            # resolution <= 16.
            ctypes_array = cast(memhandle, POINTER(c_ushort))
        else:
            # Use the win_buf_alloc_32 method for devices with a resolution > 16
            memhandle = ul.win_buf_alloc_32(total_count)
            # Convert the memhandle to a ctypes array.
            # Use the memhandle_as_ctypes_array_32 method for devices with a
            # resolution > 16
            ctypes_array = cast(memhandle, POINTER(c_ulong))
        
        # Check if the buffer was successfully allocated
        if not memhandle:
            raise Exception('Failed to allocate memory')
        
        ul.a_in_scan(
            self.board_num, low_chan, high_chan, total_count,
            self.sampling_rate, ai_range, memhandle, scan_options)
        if self.status:
            print('Scan completed successfully.')
        
        data = np.zeros((points_per_channel,num_chans))
        tlist = np.linspace(0,self.measurement_time,num = points_per_channel,endpoint = True)
        
        # Print the data
        data_index = 0
        for i in range(points_per_channel):
            for j in range(num_chans):
                eng_value = ul.to_eng_units(self.board_num, ai_range, ctypes_array[data_index])
                data[i,j] = eng_value
                data_index += 1
        if self.status:
            print('Data copied from buffer - complete.')
        
        if memhandle:
            # Free the buffer in a finally block to prevent  a memory leak.
            ul.win_buf_free(memhandle)
        
        return tlist, data
    
    def scan_exttrigger(self):
        points_per_channel = int(self.measurement_time * self.sampling_rate)
        memhandle = None
        ai_info = self.daq_dev_info.get_ai_info()
        low_chan = 0
        high_chan = min(3, ai_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1
        total_count = points_per_channel * num_chans

        ai_range = ai_info.supported_ranges[self.voltage_range]
        scan_options = ScanOptions.CONTINUOUS | ScanOptions.BACKGROUND | ScanOptions.EXTTRIGGER
        memhandle = ul.win_buf_alloc(total_count)
        ctypes_array = cast(memhandle, POINTER(c_ushort))
        
        # Check if the buffer was successfully allocated
        if not memhandle:
            raise Exception('Failed to allocate memory')
            
        if self.status:
            print('Waiting for a trigger...')
        
        ul.a_in_scan(
            self.board_num, low_chan, high_chan, total_count,
            self.sampling_rate, ai_range, memhandle, scan_options)
        
        status, curr_count, curr_index = ul.get_status(self.board_num, FunctionType.AIFUNCTION)
        
        while status != Status.IDLE and curr_count < total_count:
            status, curr_count, curr_index = ul.get_status(self.board_num, FunctionType.AIFUNCTION)
            
        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
        
        if self.status:
            print('Scan completed successfully.')
        
        data = np.zeros((points_per_channel,num_chans))
        tlist = np.linspace(0,self.measurement_time,num = points_per_channel,endpoint = True)
        
        # Print the data
        data_index = 0
        for i in range(points_per_channel):
            for j in range(num_chans):
                eng_value = ul.to_eng_units(self.board_num, ai_range, ctypes_array[data_index])
                data[i,j] = eng_value
                data_index += 1
        if self.status:
            print('Data copied from buffer - complete.')
        
        if memhandle:
            # Free the buffer in a finally block to prevent  a memory leak.
            ul.win_buf_free(memhandle)
        
        return tlist, data
    
    def scan_trigger_ch0(self):
        points_per_channel = int(self.measurement_time * self.sampling_rate)
        memhandle = None
        ai_info = self.daq_dev_info.get_ai_info()
        low_chan = 0
        high_chan = min(3, ai_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1
        total_count = points_per_channel * num_chans
        
        trig_type = TrigType.TRIG_ABOVE
        low_threshold_volts = 0.1
        high_threshold_volts = 0.3

        ai_range = ai_info.supported_ranges[self.voltage_range]
        scan_options = ScanOptions.EXTTRIGGER
        
        memhandle = ul.win_buf_alloc(total_count)
        ctypes_array = cast(memhandle, POINTER(c_ushort))
        
        # Check if the buffer was successfully allocated
        if not memhandle:
            raise Exception('Failed to allocate memory')
        
        low_threshold, high_threshold = self.get_threshold_counts(ai_range, low_threshold_volts, high_threshold_volts)
        ul.set_trigger(self.board_num, trig_type, low_threshold, high_threshold)
        ul.a_in_scan(self.board_num, low_chan, high_chan, total_count, self.sampling_rate, ai_range, memhandle, scan_options)
        
        if self.status:
            print('Scan completed successfully.')
        
        data = np.zeros((points_per_channel,num_chans))
        tlist = np.linspace(0,self.measurement_time,num = points_per_channel,endpoint = True)
        
        # Print the data
        data_index = 0
        for i in range(points_per_channel):
            for j in range(num_chans):
                eng_value = ul.to_eng_units(self.board_num, ai_range, ctypes_array[data_index])
                data[i,j] = eng_value
                data_index += 1
        if self.status:
            print('Data copied from buffer - complete.')
        
        if memhandle:
            # Free the buffer in a finally block to prevent  a memory leak.
            ul.win_buf_free(memhandle)
        
        return tlist, data
    
    def get_threshold_counts(self, ai_range, low_threshold_volts, high_threshold_volts):
        
        ai_info = self.daq_dev_info.get_ai_info()
        ai_range = ai_info.supported_ranges[self.voltage_range]
        
        if ai_info.analog_trig_resolution == 0:
            # If the trigger resolution from AnalogInputProps is 0,
            # the resolution of the trigger is the same as the
            # analog input resolution, and we can use from_eng_units
            # to convert from engineering units to count
            low_threshold = ul.from_eng_units(self.board_num, ai_range,
                                              low_threshold_volts)
            high_threshold = ul.from_eng_units(self.board_num, ai_range,
                                               high_threshold_volts)
        else:
            # Otherwise, the resolution of the triggers are different
            # from the analog input, and we must convert from engineering
            # units to count manually

            trig_range = ai_info.analog_trig_range
            if trig_range == ULRange.UNKNOWN:
                # If the analog_trig_range is UNKNOWN, the trigger voltage
                # range is the same as the analog input.
                trig_range = ai_range

            low_threshold = self.volts_to_count(
                low_threshold_volts, ai_info.analog_trig_resolution,
                trig_range)
            high_threshold = self.volts_to_count(
                high_threshold_volts, ai_info.analog_trig_resolution,
                trig_range)

        return low_threshold, high_threshold
    
    def volts_to_count(self, volts, resolution, voltage_range):
        full_scale_count = 2 ** resolution
        range_min = voltage_range.range_min
        range_max = voltage_range.range_max
        return int((full_scale_count / (range_max - range_min) * (volts - range_min)))

if __name__ == '__main__':
    run_example()
