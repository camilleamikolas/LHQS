# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 14:18:41 2020

@author: crow104
"""

import numpy as np
import matplotlib.pyplot as plt
import pyvisa
import os
import datetime
import csv

# C:\Users\crow104\python\instruments\pmh_test0.py
#
# P. M. Harrington, 10 October 2018

class Smith_data():
    def __init__(self, vna_smith_data, freq_range=None):
        self.smith = vna_smith_data
        self.real = np.array( vna_smith_data[0::2] )
        self.imag = np.array( vna_smith_data[1::2] )
        num_points = self.real.size

        self.complex = self.real + 1j*self.imag        
        self.linm = abs(self.complex)
        self.logm = 20*np.log10(abs(self.complex))
        self.phase = np.arctan2(self.imag, self.real)
        self.uphase = np.unwrap(self.phase)
              
        if freq_range:
            self.freq = np.linspace(freq_range[0], freq_range[1], num_points)
        else:
            self.freq = None                
    ##END __init__
##END Smith_data
        
def get_hardcoded_address():
    return "GPIB::2::INSTR"

def test_vna():
    address = get_hardcoded_address()
    rm = pyvisa.ResourceManager()
    instr = rm.open_resource(address)
    instr.write("*IDN?")
    vals = instr.read()
    print(vals)
    instr.close()

def get_save_path():
    path0 = r"C:\Data\2020\200305_admx_wilk_package_v2_rm_temp_vna"
    time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = path0 + "\\vna_" + time_str
    return save_path
    
def get_smith():
    #
    address = get_hardcoded_address()
    rm = pyvisa.ResourceManager()
    instr = rm.open_resource(address)

    #
    instr.write("form asc,0")
    string_data = instr.query('CALC1:DATA? SDATA;')
    numerical_data = np.array(string_data.split(','), dtype='float')

    # get frequency range
    freq_start = float(instr.query('sense:freq:start?'))
    freq_stop = float(instr.query('sense:freq:stop?'))
    freq_range = [freq_start, freq_stop]
    
    #
    instr.close()
    
    #
    smith = Smith_data(numerical_data, freq_range)
    
    plt.figure()
    x = 1e-9*smith.freq
    y = smith.logm
    plt.plot(x, y)
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("LogMag (dB)")
    
    return smith

def save_smith(smith_data_in, save_path=None):    
    #
    if save_path is None:
        save_path = get_save_path()
    
    if (not os.path.isdir(save_path)):
            os.mkdir(save_path)
    
    #
    data_to_save = np.vstack(zip(
            smith_data_in.freq, smith_data_in.real, smith_data_in.imag))
    file_path = save_path + "\\" + "smith.txt"
    header = ("freq_Hz", "real", "imag") #("N_list", "e_gnd", "e_gap")
    table = []
    for idx, d in enumerate(data_to_save):
        table.append(d)
    table.insert(0, header)
    f = open(file_path, "w", newline="")
    writer = csv.writer(f)
    writer.writerows(table)
    f.close()
    
    #
    data_to_save = smith_data_in.comment
    file_path = save_path + "\\" + "_readme.txt"
    header = () #("N_list", "e_gnd", "e_gap")
    table = []
    table.append([data_to_save])

    table.insert(0, header)
    f = open(file_path, "w", newline="")
    writer = csv.writer(f)
    writer.writerows(table)
    f.close()
    
if __name__=="__main__":
    s = get_smith()
    s.comment = "S22, port 1 (input port far right #4), port 2 (input port second from left #2), with cover"
    save_smith(s)

    