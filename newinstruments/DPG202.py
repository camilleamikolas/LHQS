#!/usr/bin/env python
"""
Created on Mon Jul 27 13:11:47 2020
( adapted from Wesley Cassidy's code https://github.com/vuthalab/CTC100 )

@author: Niyaz Beysengulov
"""

import serial
import numpy as np
import time
timestr = time.strftime("%Y%m%d-%H%M%S")



""" Functions to communicate with DPG202 pressure controller over SERIAL port (USB)"""
    
def DPG202(port):
    instrument = serial.Serial(
    port, 
    baudrate=9600, 
    timeout=1, 
    bytesize=8, 
    parity ='N', 
    stopbits=1, 
    xonxoff=False, 
    dsrdtr=False
    )
    return instrument
    
    
def write_comm(self, command):
    """
    Write a command to the DPG202 over serial, then wait for the
    response.
    """
    comm = command
    command_ascii = comm.encode('ascii')
    self.write(command_ascii)
    try:
        self.inWaiting()
    except:
        print("Lost connection!")
    response = self.read_until('\r')
    return response
    
def measure(self, channel):
    if(channel == "Pressure1"):
        ch = 1
    else:
        ch = 2
    c =  "{:03d}00{:03d}02=?".format(ch, 740)
    c += "{:03d}\r".format(sum([ord(x) for x in c])%256)
        
    # sending command for reading
    r_encoded = write_comm(self, c)
    r = r_encoded.decode()
        
    # Check the length
    if(len(r) < 20):
        raise ValueError("gauge response too short to be valid")

    # Check it is terminated correctly
    #if(r[-1] != "\r"):
    #    raise ValueError("gauge response incorrectly terminated")

    # Evaluate the checksum
    if(int(r[-4:-1]) != (sum([ord(x) for x in r[:-4]])%256)):
        raise ValueError("invalid checksum in gauge response")

    # Pull out the address, parameter and data
    rchannel   = int(r[:3])
    rw         = int(r[3:4])
    rparam_num = int(r[5:8])
    rdata      =  r[10:-4]

    # Check for errors
    if(rdata == "NO_DEF"):
        raise ValueError("undefined parameter number")
    if(rdata == "_RANGE"):
        raise ValueError("data is out of range")
    if(rdata == "_LOGIC"):
        raise ValueError("logic access violation")
    if(rchannel!=ch or rw!=1 or rparam_num!=740):
        raise ValueError("invalid response from gauge")

    # Convert to a float
    mantissa = int(rdata[:4])/1000.0
    exponent = int(rdata[4:])

    return float(mantissa*10**(exponent-20))*0.7463

if __name__=="__main__":
    t = Instrument ('COM6')
    print(t.measure('Pressure2'))
    t.close()