import os
import pandas as pd
import numpy as np
from datetime import datetime

class BlueFors():

    def __init__(self):
        
        self.folder_path = r'C:\Users\LHQS3\Documents\BlueForsLogs\logs'
        current_date_time = datetime.now()
        self.date = current_date_time.date().strftime(r"%y-%m-%d")
        self.time = current_date_time.time().strftime(r'%H:%M:%S')
        self.folder_name = os.path.basename(self.get_latest_subdir())

    def get_latest_subdir(self):
        b = self.folder_path
        all_subdirs =[]
        for d in os.listdir(b):
            bd = os.path.join(b, d)
            if os.path.isdir(bd): all_subdirs.append(bd)
        latest_subdir = max(all_subdirs, key=os.path.getmtime)
        return latest_subdir

    #def get_subdirs_multiple(self, date1, date2):
    #    b = self.folder_path
    #    d1 = int(date1[6:])
    #    d2 = int(date2[6:])
    #    num_folders = d2-d1
    #    subdirs_list =[]
    #    for i in range(num_folders):
    #        subdirs_list[i] = f'{b}\{date1[:5]}-{int(date1[6:])+i}'
    #        return subdirs_list

    
    def get_last_measured_time(self):
        self.folder_name = os.path.basename(self.get_latest_subdir())
        file_path = os.path.join(self.folder_path, self.folder_name, 'CH1 T '+self.folder_name+'.log')
        try:
            df = pd.read_csv(file_path,
                            delimiter = ',',
                            names     = ['date', 'time', 'temperature'],
                            header    = None
            )
            
            # There is a space before the day
            df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')
            return df.iloc[-1]['time']
        except (PermissionError, OSError) as err:
            self.log.warn('Cannot access log file: {}. Returning np.nan instead of temperature value.'.format(err))
            return np.nan
        except IndexError as err:
            self.log.warn('Cannot parse log file: {}. Returning np.nan instead of temperature value.'.format(err))
            return np.nan
    
    #def get_temperature_in_timeframe(self, date1, date2, time1, time2, channel: int) -> tuple:
    #    self.folder_name = os.path.basename(self.get_latest_subdir())
    #    file_path = os.path.join(self.folder_path, self.folder_name, 'CH1 T '+self.folder_name+'.log')
    #    try:
    #        df = pd.read_csv(file_path,
    #                        delimiter = ',',
    #                        names     = ['date', 'time', 'temperature'],
    #                        header    = None
    #        )
    #        
    #        # There is a space before the day
    #        df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')
    #        return df.iloc[-1]['time']
    #    except (PermissionError, OSError) as err:
    #        self.log.warn('Cannot access log file: {}. Returning np.nan instead of temperature value.'.format(err))
    #        return np.nan
    #    except IndexError as err:
    #        self.log.warn('Cannot parse log file: {}. Returning np.nan instead of temperature value.'.format(err))
    #        return np.nan


    def get_temperature(self, channel: int) -> float:
        self.folder_name = os.path.basename(self.get_latest_subdir())
        file_path = os.path.join(self.folder_path, self.folder_name, 'CH'+str(channel)+' T '+self.folder_name+'.log')
        try:
            df = pd.read_csv(file_path,
                            delimiter = ',',
                            names     = ['date', 'time', 'temperature'],
                            header    = None
            )
            
            # There is a space before the day
            df.index = pd.to_datetime(df['date']+'-'+df['time'], format=' %d-%m-%y-%H:%M:%S')
            return df.iloc[-1]['temperature']
        except (PermissionError, OSError) as err:
            self.log.warn('Cannot access log file: {}. Returning np.nan instead of temperature value.'.format(err))
            return np.nan
        except IndexError as err:
            self.log.warn('Cannot parse log file: {}. Returning np.nan instead of temperature value.'.format(err))
            return np.nan


    
    def get_pressure(self, channel: int) -> float:
        self.folder_name = os.path.basename(self.get_latest_subdir())
        file_path = os.path.join(self.folder_path, self.folder_name, 'maxigauge '+self.folder_name+'.log')
        try:
            df = pd.read_csv(file_path,
                            delimiter=',',
                            names=['date', 'time',
                                    'ch1_name', 'ch1_void1', 'ch1_status', 'ch1_pressure', 'ch1_void2', 'ch1_void3',
                                    'ch2_name', 'ch2_void1', 'ch2_status', 'ch2_pressure', 'ch2_void2', 'ch2_void3',
                                    'ch3_name', 'ch3_void1', 'ch3_status', 'ch3_pressure', 'ch3_void2', 'ch3_void3',
                                    'ch4_name', 'ch4_void1', 'ch4_status', 'ch4_pressure', 'ch4_void2', 'ch4_void3',
                                    'ch5_name', 'ch5_void1', 'ch5_status', 'ch5_pressure', 'ch5_void2', 'ch5_void3',
                                    'ch6_name', 'ch6_void1', 'ch6_status', 'ch6_pressure', 'ch6_void2', 'ch6_void3',
                                    'void'],
                            header=None)

            df.index = pd.to_datetime(df['date']+'-'+df['time'], format='%d-%m-%y-%H:%M:%S')

            return df.iloc[-1]['ch'+str(channel)+'_pressure']
        except (PermissionError, OSError) as err:
            self.log.warn('Cannot access log file: {}. Returning np.nan instead of the pressure value.'.format(err))
            return np.nan
        except IndexError as err:
            self.log.warn('Cannot parse log file: {}. Returning np.nan instead of the pressure value.'.format(err))
            return np.nan

    def get_time_stamp(self):
        self.folder_name = os.path.basename(self.get_latest_subdir())
        output_text = f'<strong>TIME</strong> \n {self.folder_name} \n {self.get_last_measured_time()} \n'
        return output_text

    def get_temperature_status(self):
        output_text = '<strong>TEMPERATURE</strong> \n'
        channels = [1, 2, 5, 6]
        for ch in channels:
            temperature = self.get_temperature(ch)
            if temperature > 100:
                output_text = output_text + f' CH{ch}  {round(temperature)} K \n'
            elif temperature > 10:
                output_text = output_text + f' CH{ch}  {round(temperature, 1)} K \n'
            elif temperature > 1:
                output_text = output_text + f' CH{ch}  {round(temperature, 2)} K \n'
            else:
                output_text = output_text + f' CH{ch}  {round(temperature * 1e3)} mK \n'
        return output_text
    
    def get_pressure_status(self):
        output_text = '<strong>PRESSURE</strong> \n'
        channels = [1, 2, 3, 4, 5, 6]
        for ch in channels:
            pressure = self.get_pressure(ch)
            if abs(pressure) < 1:
                output_text = output_text + f' P{ch}  {pressure:.2e} mbar \n'
            elif abs(pressure) < 10:
                output_text = output_text + f' P{ch}  {round(pressure, 1)} mbar \n'
            else:
                output_text = output_text + f' P{ch}  {round(pressure)} mbar \n'
        return output_text
    
    def get_status_all(self):
        return self.get_time_stamp() + '\n' + self.get_temperature_status() + '\n' + self.get_pressure_status()


if __name__ == '__main__':
    fridge = BlueFors()
    #print(fridge.get_temperature(1))
    #print(fridge.get_pressure(1))
    #print(fridge.get_time_stamp())
    #print(fridge.get_temperature_status())
    #print(fridge.get_pressure_status())
    print(fridge.get_status_all())