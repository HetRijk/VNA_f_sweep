# -*- coding: utf-8 -*-
"""
Created on Mon Oct  1 11:22:18 2018

@author: Rijk

DESCRIPTION
Shortened VISA functions for the A.09.33.07 command set
Made for the Agilent/Keysight PNA Network Analyzer E8361C

COMMENTS
1.  Adding channels cannot be done inside the SCPI command set. 
    Therefore only the first channel is used and the default is 1 and should not be changed.
    The parameter was left in case a solution for this is found.

"""

import visa
import time
import sys
import numpy as np

#channel_num = 1

## Resets the VNA
def reset(instrument):
    """Resets the instrument"""
    instrument.write('*RST')
    
## Clears the VNA
def clear(instrument):
    """Clears the instrument"""
    instrument.write('*CLS')
    
## 
def connect(address='GPIB0::16::INSTR'):
    """Sets up connection to the instrument at the address"""
    rm = visa.ResourceManager()
    return rm.open_resource(address)
    
# =============================================================================
# Controlling windows    
# =============================================================================

def display_window(instrument, window_num=1, status='ON'):
    """Turns a window on the instrument 'on' or 'off' """
    status.upper()
    if window_num != 1:
        command = ':DISPlay:WINDow%d:STATe %s' % (window_num, status)
        instrument.write(command)
        
def autoscale(instrument, trace_num):
    """Performs autoscaling for a single trace"""
    command = ':DISPlay:WINDow:TRACe%s:Y:AUTO' % (trace_num)
    instrument.write(command)
    
# =============================================================================
# Control measurements
# =============================================================================

def meas_close_all(instrument):
    command = ':CALCulate:PARameter:DELete:ALL'
    instrument.write(command)

def meas_create(instrument, meas_name, s_parameters, channel_num=1):
    """Create a measurement of the S-parameters for the instrument"""
    command = ':CALCulate%d:PARameter:DEFine:EXTended "%s","%s"' % (channel_num, meas_name, s_parameters)
    instrument.write(command)
    
def meas_show(instrument, meas_name, window_num=1, trace_num=9):
    """Shows the measuremnt to a window as a numbered trace, so it's displayed there"""
    command = ':DISPlay:WINDow%d:TRACe%d:FEED "%s"' % (window_num, trace_num, meas_name)
    instrument.write(command)
    
def meas_start(instrument):
    """Start measurement by turning on the RF power of the source"""
    command = ':OUTPut:STATe %d' % (1)
    instrument.write(command)

# =============================================================================
# Set measurement parameters
# =============================================================================

def set_amplitude(instrument, amplitude, unit='DBM', channel_num=1):
    """Sets output amplitude of the instrument in unit given"""
    command = ':SOURce%d:POWer:LEVel:IMMediate:AMPLitude %G %s' % (channel_num, amplitude, unit)
    instrument.write(command)
    
def set_Df_sweep(instrument, f_start, f_stop, unit='MHZ', channel_num=1):
    """Sets start and stop frequency of sweep of channel"""
    command1 = ':SENSe%d:FREQuency:STARt %G %s' % (channel_num, f_start, unit)
    command2 = ':SENSe%d:FREQuency:STOP %G %s' % (channel_num, f_stop, unit)
    instrument.write(command1)
    instrument.write(command2)
    
def set_f_start(instrument, f_start, unit='MHZ', channel_num=1):
    """Sets start frequency of sweep of channel"""
    command = ':SENSe%d:FREQuency:STARt %G %s' % (channel_num, f_start, unit)
    instrument.write(command)
    
def set_f_stop(instrument, f_stop, unit='MHZ', channel_num=1):
    """Sets stop frequency of sweep of channel"""
    command = ':SENSe%d:FREQuency:STOP %G %s' % (channel_num, f_stop, unit)
    instrument.write(command)

def set_num_points(instrument, num_points='MAXimum', channel_num=1):
    """Sets number of data points for a given channel"""
    command = ':SENSe%d:SWEep:POINts %s' % (channel_num, num_points)
    instrument.write(command)
    
def set_if_bandwidth(instrument, if_bandwidth, window_num=1, channel_num=1):
    """"Sets the bandwidth in Hz of the intermediate frequency (IF) bandpass filter, low values lead to slow measurements"""
    command = ':SENSe%s:BANDwidth:RESolution %G HZ' % (window_num, if_bandwidth)
    instrument.write(command)
    
# =============================================================================
# Calibration
# =============================================================================    
    
def cal_load(instrument, cal_name):
    calsets = get_cal_sets(instrument)
    if cal_name not in calsets:
        sys.exit('Calibration set %s not found' % (cal_name)) 
    else:
        command = ':SENSe:CORRection:CSET:ACTivate "%s",%d' % (cal_name, 1)
        instrument.write(command)

# =============================================================================
# Saving files
# =============================================================================
    
def save_local(instrument, file_path, file_type='CSV Formatted Data', scope='Auto', file_format='Displayed', selector=1):
    command = ':MMEMory:STORe:DATA "%s","%s","%s","%s",%d' % (file_path, file_type, scope, file_format, selector)
    instrument.write(command)

# =============================================================================
# Queries
# =============================================================================

def get_meas_data(instrument, meas_name, data_type='SDATA', channel_num=1):
    """Queries measurement data and parses data if data is complex"""
    command = ':CALCulate%d:PARameter:SELect "%s"' % (channel_num, meas_name)
    instrument.write(command)
    data = instrument.query_ascii_values(':CALCulate:DATA? %s' % (data_type))
    
    if data_type == 'SDATA':
        data_real   = data[::2]
        data_imag   = data[1::2]
        data        = np.array([data_real, data_imag])
        
    return data

def get_Df(instrument):
    """Queries for start and stop frequencies"""
    f_start     = instrument.query_ascii_values(':SENSe:FREQuency:STARt?')[0]
    f_stop      = instrument.query_ascii_values(':SENSe:FREQuency:STOP?')[0]
    return f_start, f_stop

def get_num_points(instrument):
    command = ':SENSe:SWEep:POINts?'
    num_points = int(instrument.query_ascii_values(command)[0])
    return num_points

def get_if_bandwidth(instrument):
    command = ':SENSe:BANDwidth:RESolution?'
    if_bandwidth = instrument.query_ascii_values(command)[0]
    return if_bandwidth

def get_meas_names(instrument):
    """Queries for all current measurement names"""
    command = ':CALCulate:PARameter:CATalog:EXTended?'
    names = instrument.query(command)
    meas_names = parse(names)[::2] 
    # Gets every other item as names also contains the s-parameter 
    # connected to the meas_name
    return meas_names


def get_cal_sets(instrument):
    """"Queries instrument for available calibration sets"""
    calsets = instrument.query(':SENSe:CORRection:CSET:CATalog? %s' % ('NAME'))
    return calsets

# =============================================================================
# Other
# =============================================================================

def parse(text, delimiter=','):
    """Did not quickly find a parser, so made one specifically for get_meas_names"""
    word_list = []
    word = ''
    for i in text:
        if i != delimiter and i != '"':
            word = word + i
        if i == delimiter or i == text[-2]:
            word_list.append(word)
            word = ''
    word_list = word_list[1:]
    return word_list


