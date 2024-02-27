
"""
-- Camille Mikolas -- 
CPW resonator + microchannel transport device experiment control, 2024
Built upon from code by Niyaz Beysengulov

Uses GPIB communication to control instruments and perform experiments.
Uses SQLite database to store data.

Estimation of experiment run time needs work. 
"""

import numpy as np
import warnings
import os.path
import os

from time import sleep, strftime
from tabulate import tabulate
from tqdm import tqdm
from IPython.display import clear_output

from helpers.database2 import Create_DB
from newinstruments.nwa2 import *

vna = E5071_2('GPIB0::2::INSTR')


def create_sweep_list(s1=0, s2=1, num=10, scale='linear'):
    if scale == 'linear':
        return np.linspace(s1, s2, num=num, endpoint=True)
    elif scale == 'log':
        return np.logspace(np.log10(s1), np.log10(s2), num=num, endpoint=True)
    else:
        warnings.warn("Warning...choose log or linear scale")


def create_path_filename(measurement_name: str):
    subdir = 'data/' + strftime("%Y-%m-%d")
    try:
        os.mkdir(subdir)
    except Exception:
        pass
    timestr = strftime("%Y-%m-%d")
    filename = timestr + "_" + measurement_name + ".db"
    filepath = os.path.join(subdir, filename)
    return filepath


class experiment():
    
    """
    Here we define the main control parameters
    """
    tconst = 0.1
    comment = 'None'
    comment2 = 'None'
    
    def __init__(self, ctrl_instrument: dict, vna_control: dict, read_instrument: dict):

        self.__reads = read_instrument
        self.__ctrls = ctrl_instrument
        self.__vnas = vna_control
        for key in ctrl_instrument:
            # create class attributes to store all control parameters
            setattr(self, key, ctrl_instrument[key][0])
        for key in vna_control:
            setattr(self, key, vna_control[key][0])


        # checking the default parameter values
        print('your experiment run options are: run(exp_name, exp_typ [1D or 2D or VNAonly], vna_type, lockin_type, savedata)')  
        print(tabulate(self.gettable_ClassAttributes()))

            
    def __len__(self):
        return len(self.list)
    

    def gettable_ClassAttributes(self) -> list:
        attr_list = []
        for attribute in dir(self):
            if attribute[:1] != '_':
                value = getattr(self, attribute)
                if not callable(value):
                    if type(value) is dict:
                        string = f"{value['val']:,} / off={value['off']:,}"
                    elif isinstance(value, (float, int)):
                        string = f"{value:,}"
                    else:
                        string = value
                    attr_list.append([attribute, string])
        return attr_list


    def instr_init(self, ramp_time=2) -> None:
        """
        initialization of instrument with user defined control attribute values
        """
        for key in list(self.__ctrls.keys()):
            attr_value = getattr(self, key)
            link = self.__ctrls[key]
            if type(attr_value) is dict:
                val = attr_value.get('val') - attr_value.get('off')       # determination of the value (including offset) to be set
            else:
                val = attr_value                                           # determination of the value to be set
            set_instument = getattr(link[1], link[3])
            set_instument(val, ramp_time)
        sleep(ramp_time)

        for key in self.__vnas.keys():
            link = self.__vnas[key]
            obj = link[1]
            method_name = link[2]    
            args = link[0]          
            # Get a reference to the method
            method = getattr(obj, method_name)
    
            # Call the method with the arguments
            method(*args)
            
        sleep(ramp_time)

        print('instruments are initialized')

    
    def __sweep_info(self, sw_st, s1, s2, num, scale, offset):
        return f"{sw_st} / {s1:,} : {s2:,} / num={num} / {scale} / off={offset:,}"

    
    def __obj_type(self, obj, index):
        if type(obj) is list:
            obj_value = obj[index]
        else:
            obj_value = obj
        return obj_value

    
    def __indexing_parameters(self, s1=0, s2=1, scale='linear', offset=0, index=0):
        start       = self.__obj_type(s1, index)
        end         = self.__obj_type(s2, index)
        scale_type  = self.__obj_type(scale, index)
        off         = self.__obj_type(offset, index)
        return start, end, scale_type, off


    def control_variables(self, control_type='sweep', var='None', s1=0, s2=1, num=10, scale='linear', offset=0):
        """
        preparing sweep lists and attributes
        """
        if type(var) is not list:
            var = [var]

        control_lists = []
        for i in range(len(var)):               
            
            first, final, scale_type, off = self.__indexing_parameters(s1, s2, scale, offset, i)
            sweep_list = create_sweep_list(first, final, num, scale_type) - off
            control_lists.append(sweep_list)
            setattr(self, var[i], self.__sweep_info(control_type, first, final, num, scale_type, off))
    
        return var, control_lists, num
        
    
    def sweep_params(self, **kwargs) -> None:
        var, control_lists, num = self.control_variables(control_type='sweep', **kwargs)
        self.__sweep = {
            'variable': var,
            'sweep lists': control_lists,
            'num points': num
        }
    
    def step_params(self, **kwargs) -> None:
        if kwargs=={}:
            var, control_lists, num = ['None'], [[0]], 1
        else:
            var, control_lists, num = self.control_variables(control_type='step', **kwargs)
        self.__step = {
            'variable': var,
            'step lists': control_lists,
            'num points': num
        }
    
    def create_sqldb(self, exp_name) -> Create_DB:
        filename = create_path_filename(exp_name)
        if os.path.exists(filename):
            os.remove(filename)

        sqldb = Create_DB(
                        filename, 
                        self.__sweep, 
                        self.__step, 
                        list(self.__reads.keys()),
                        self.gettable_ClassAttributes()
        )
        return sqldb
    
    def close_sqldb(self, sqldb: Create_DB) -> None:
        sqldb.sql_close()

    def find_keys_with_val(self, dictionary, word):
        keys_with_val = []
        for key, values in dictionary.items():
            for value in values:
                if word in str(value):
                    keys_with_val.append(key)
                    break
        return keys_with_val

    def remove_read_instr(self, instr):
        instrument = instr
        if instrument in self.__reads.keys():
            del self.__reads[instrument]
        else:
            pass
    
    def add_read_instr(self, instr, vals):
        instrument = instr
        values = vals
        if instrument in self.__reads.keys():
            pass
        else:
            self.__reads[instrument] = values
        return self.__reads

    def reset_vna(self):
        out = vna.get_output()
        if out: 
            vna.set_output('OFF')
        else:
            pass

    def vna_sleep_time(self):
        vna_controls = self.__vnas
        vna_sweep_points = int(vna_controls.get('sweep_pts')[0][0])
        vna_num_avgs = int(vna_controls.get('num_avg')[0][0])

        if vna_sweep_points < 6000:
            if vna_controls.get('avg')[0][0] == 'OFF':
                vna_sleep_time = (0.25)
            if vna_controls.get('avg')[0][0] == 'ON':
                if vna_num_avgs < 50:
                    vna_sleep_time = (9)
                else:
                    vna_sleep_time = (vna_sweep_points/(vna_num_avgs*10))
        if vna_sweep_points > 6000:
            if vna_controls.get('avg')[0][0] == 'OFF':
                vna_sleep_time = (1)
            if vna_controls.get('avg')[0][0] == 'ON':
                vna_sleep_time = (vna_sweep_points/(vna_num_avgs*10))

        return vna_sleep_time
        

    def vna_readout_adjust(self):
        # check vna format and adjust readout keys
        vna_controls = self.__vnas
        form = vna_controls.get('format')[0][0]
        readouts = self.__reads
        rkeys = list(readouts.keys())
        r_vnakeys = [key for key in rkeys if 'vna' in key]

        if form in ['SMIT', 'POL', 'SADM']:
            if len(r_vnakeys) == 3:
                pass
            elif len(r_vnakeys) == 2 and 'vna_freq' and 'vna_y1' in r_vnakeys:
                readouts['vna_y2'] = [vna, 'read_data_y2', 'U']
            else:
                print('please add correct vna readout keys in the readout dictionary')

        else:
            if len(r_vnakeys) == 3 and 'vna_freq' and 'vna_y1' and 'vna_y2' in r_vnakeys:
                del readouts['vna_y2']
            elif len(r_vnakeys) == 2 and 'vna_freq' and 'vna_y1' in r_vnakeys:
                pass
            else:
                print('please add correct vna readout keys in the readout dictionary')
        
        rkeys = list(readouts.keys())
        r_vnakeys = [key for key in rkeys if 'vna' in key]

        return r_vnakeys
    
    def VNA_run_only(self, exp_name, exp_type, savedata):

        sweep_controls  = {key: self.__ctrls.get(key) for key in self.__sweep['variable']}
        step_controls   = {key: self.__ctrls.get(key, None) for key in self.__step['variable']}
        readouts        = self.__reads
        
        sweep_lists = self.__sweep.get('sweep lists')
        step_lists  = self.__step.get('step lists')

        num_sweep_points = self.__sweep.get('num points')
        num_step_points  = self.__step.get('num points')

        vna_controls = self.__vnas
        self.vna_readout_adjust()

        reads = self.__reads
        controls = self.__ctrls
        control_keys = list(controls.keys())
        control_vals = [controls.get(control_keys[i]) for i in range(len(control_keys))]
        rem_keys = [key for key in reads if 'vna' not in key]

        if len(rem_keys) > 0:
            vals = [self.__reads.get(rem_keys[i]) for i in range(len(rem_keys))]
            for i in range(len(rem_keys)):
                k = rem_keys[i]
                self.remove_read_instr(k)
        if len(control_keys) > 0:
            for i in range(len(control_keys)):
                k = control_keys[i]
                del self.__ctrls[k]
        
            vna.set_output('ON')
            sleep(1)

        if savedata:
            sqldb = self.create_sqldb(exp_name)  

            try:
                vna_arr = []
                for key, instr in reads.items():
                    if 'vna' in key:
                        data = getattr(instr[0], instr[1])()
                        vna_arr.append([data])
                    else:
                        pass
                vna_arr = np.array(vna_arr).transpose()

                for i in range(len(vna_arr)):
                    v = vna_arr[i]
                    for k in range(len(v)):
                        sub_arr = [i, 0] + v[k].tolist()
                        # write data into sql_db
                        if savedata:
                            sqldb.sql_sweep_write('table_data', tuple(sub_arr))
                
                if savedata:
                    print('experiment is successfully finished')

                for i in range(len(rem_keys)):
                    self.add_read_instr(rem_keys[i], vals[i])

                for i in range(len(control_keys)):
                    if control_keys[i] in controls.keys():
                        pass
                    else:
                        self.__ctrls[control_keys[i]] = control_vals[i]

            except KeyboardInterrupt:
                print ('KeyboardInterrupt exception is caught / data aqcuisiotion is stopped by user')

            finally:
                if savedata:
                    sqldb.sql_close()
                    print('closed db')      

        
    def noVNA_run_init(self):
        reads = self.__reads
        rem_keys = [key for key in reads if 'vna' in key]

        if len(rem_keys) > 0:
            vals = [self.__reads.get(rem_keys[i]) for i in range(len(rem_keys))]
            for i in range(len(rem_keys)):
                k = rem_keys[i]
                self.remove_read_instr(k)
        return rem_keys, vals
                    
    
    def noVNA_run_final(self, rem_keys, vals):
        for i in range(len(rem_keys)):
            self.add_read_instr(rem_keys[i], vals[i])


    def noVNA_run_main(self, exp_name, exp_type, num_sweep_points, num_step_points, savedata):

        sweep_controls  = {key: self.__ctrls.get(key) for key in self.__sweep['variable']}
        step_controls   = {key: self.__ctrls.get(key, None) for key in self.__step['variable']}
        readouts        = self.__reads
        
        sweep_lists = self.__sweep.get('sweep lists')
        step_lists  = self.__step.get('step lists')

        num_sweep_points = self.__sweep.get('num points')
        num_step_points  = self.__step.get('num points')

        rem_keys, vals = self.noVNA_run_init()

        if exp_type == '1D':
            self.step_params()

        progress_step = None

        if savedata:
            sqldb = self.create_sqldb(exp_name)


        try:
            for i in range(num_step_points):
                if exp_type == '2D':
                    clear_output(wait=True)

                    progress_step = 'loop ' + str(i + 1)+'/'+str(num_step_points)

                    # set experiment controls for 2D depending on if Vac will be the parameter swept

                    if 'Vac' in self.sweep_params['variable']:
                        #set step control instruments
                        for instr, step_list in zip(list(step_controls.values()), step_lists):
                            setattr(instr[1], instr[2], step_list[i])

                        #ramp sweep control instruments to initial sweep point and wait 5 seconds
                        for instr, sweep_list in zip(list(sweep_controls.values()), sweep_lists):
                            instr_ramp = getattr(instr[1], instr[3])
                            instr_ramp(sweep_list[0])
                        sleep(5)

                    else:
                        #set step control instruments
                        for instr, step_list in zip(list(step_controls.values()), step_lists):
                            setattr(instr[1], instr[2], step_list[i])

                        #ramp sweep control instruments to initial sweep point and wait 5 seconds
                        for instr, sweep_list in zip(list(sweep_controls.values()), sweep_lists):
                            instr_ramp = getattr(instr[1], instr[3])
                            instr_ramp(sweep_list[0])
                        sleep(5)

                #set inner sweep loop        
                for j in tqdm(range(num_sweep_points), ncols = 100, desc = progress_step):

                    #set sweep control instruments
                    for instr, sweep_list in zip(list(sweep_controls.values()), sweep_lists):
                        setattr(instr[1], instr[2], sweep_list[j])
                    sleep(3 * self.tconst)

                    #measure readout instruments
                    data_instance = [j, i]
                    for instr in list(readouts.values()):
                        data = getattr(instr[0], instr[1])
                        data_instance.append(data)
                    
                    #write into sql database
                    if savedata:
                        sqldb.sql_sweep_write('table_data', tuple(data_instance))

                if savedata:
                    print('experiment is successfully finished')

        except KeyboardInterrupt:
            print ('KeyboardInterrupt exception is caught / data aqcuisiotion is stopped by user')

        finally:
            if savedata:
                sqldb.sql_close()
                print('closed db')                    


        self.noVNA_run_final(rem_keys, vals)

        
    def vna_run_main(self, exp_name, exp_type, num_sweep_points, lockin_type, savedata):

        vna_controls  = {key: self.__vnas.get(key) for key in self.__vnas.keys()}
        self.vna_readout_adjust()

        #check vna sweep points
        vna_sweep_points = vna_controls.get('sweep_pts')[0][0]

        sweep_controls  = {key: self.__ctrls.get(key) for key in self.__sweep['variable']}
        readouts        = self.__reads
        
        sweep_lists = self.__sweep.get('sweep lists')

        num_sweep_points = self.__sweep.get('num points')
        vna_sleep = self.vna_sleep_time()

        reads = self.__reads

        if not lockin_type:
            rem_keys = [key for key in reads if 'vna' not in key]
            if len(rem_keys) > 0:
                vals = [self.__reads.get(rem_keys[i]) for i in range(len(rem_keys))]
                for i in range(len(rem_keys)):
                    k = rem_keys[i]
                    self.remove_read_instr(k)

        print(reads)

        if savedata:
            sqldb = self.create_sqldb(exp_name)

        progress_step = None
        counter  = 0

        if exp_type == '1D':
            try:
                for i in range(num_sweep_points):

                    clear_output(wait=True)

                    progress_step = 'loop ' + str(i + 1)+'/'+str(num_sweep_points)

                    # ramp sweep control instruments to initial sweep point and wait 5 seconds
                    for instr, sweep_list in zip(list(sweep_controls.values()), sweep_lists):
                        instr_ramp = getattr(instr[1], instr[3])
                        instr_ramp(sweep_list[i]) 
                    sleep(5)

                    self.reset_vna()

                    # set sweep instrument to ith value in sweep list
                    for instr, sweep_list in zip(list(sweep_controls.values()), sweep_lists):
                        setattr(instr[1], instr[2], sweep_list[i])
                    sleep(3 * self.tconst)

                    vna.set_output('ON')
                    sleep(vna_sleep)

                    vna_arr = []
                    lockin_arr = []
                    for key, instr in readouts.items():
                        if 'vna' in key:
                            data = getattr(instr[0], instr[1])()
                            vna_arr.append([data])
                        else:
                            data = getattr(instr[0], instr[1])
                            lockin_arr.append(data)

                    lockin_arr = list(lockin_arr)
                    lockin_arr = np.array(lockin_arr).transpose()
                    vna_arr = np.array(vna_arr).transpose()

                    if not lockin_arr.any():
                        for j in tqdm(range(len(list(vna_arr))), ncols = 100, desc = progress_step):
                            v = vna_arr[j]
                            for k in range(len(list(v))):
                                sub_arr = [counter, i] + v[k].tolist()
                                counter += 1
                                # write data into sql_db
                                if savedata:
                                    sqldb.sql_sweep_write('table_data', tuple(sub_arr))

                    else:
                        for j in tqdm(range(len(list(vna_arr))), ncols = 100, desc = progress_step):
                            v = vna_arr[j]
                            for k in range(len(v)):
                                sub_arr = [counter, i, lockin_arr[0], lockin_arr[1]] + v[k].tolist()
                                counter += 1   
                                # write data into sql_db
                                if savedata:
                                    sqldb.sql_sweep_write('table_data', tuple(sub_arr))
                    
                    counter = counter

            except KeyboardInterrupt:
                print ('KeyboardInterrupt exception is caught / data aqcuisiotion is stopped by user')

            finally:
                if savedata:
                    sqldb.sql_close()
                    print('closed db')

            if not lockin_type:
                for i in range(len(rem_keys)):
                    self.add_read_instr(rem_keys[i], vals[i])
        
        else:
            print('i havent coded this yet')
          
        

    def run(self, exp_name = 'sweep_0', exp_type = '1D', vna_type = True, lockin_type = True, savedata = True):
        # run experiment of type 1D or 2D with or without VNA or lockin.

        exp_t = exp_type
        exp_n = exp_name
        
        if exp_t == '1D' and not vna_type:
            self.step_params()

        sweep_controls  = {key: self.__ctrls.get(key) for key in self.__sweep['variable']}
        step_controls   = {key: self.__ctrls.get(key, None) for key in self.__step['variable']}
        readouts = self.__reads

        sweep_lists = self.__sweep.get('sweep lists')
        step_lists  = self.__step.get('step lists')

        num_sweep_points = self.__sweep.get('num points')
        num_step_points  = self.__step.get('num points')

        if lockin_type and not vna_type:
            # run experiment without VNA either 1D or 2D
            self.noVNA_run_main(exp_n, exp_t, num_sweep_points, num_step_points, savedata)


        elif vna_type and exp_t != 'VNAonly':
            # run experiment with VNA
            self.vna_run_main(exp_n, exp_t, num_sweep_points, lockin_type, savedata)
        
        elif exp_type == 'VNAonly':
            self.VNA_run_only(exp_n, exp_t, savedata)

        vna.set_output('OFF')
            
    def estimate_run_time(self, exp_type='1D', vna_type = False):
        vna_controls    = {key: self.__vnas.get(key) for key in self.__vnas.keys()}

        if exp_type=='1D' and not vna_type:
            self.step_params()
            num_sweep_points = self.__sweep.get('num points')
            num_step_points  = self.__step.get('num points')
            exp_time_sec = (3 * self.tconst * num_sweep_points * num_step_points + (4 + 2) * (num_step_points - 1)) * 1.2
        if exp_type=='1D' and vna_type:
            steps = self.step_params()
            num_sweep_points = self.__sweep.get('num points')
            num_step_points  = self.__step.get('num points')
            vna_sweep_points = vna_controls.get('sweep_pts')[0][0]
            loop_times = 5.5
            num_sweep_points = self.__sweep.get('num points')
            exp_time_sec = (num_sweep_points*loop_times) + (vna_sweep_points*loop_times)/10

        # factor 1.2 is empirical (due to some execution time of the code)
        if exp_time_sec > 3600:
            exp_time = [round(exp_time_sec/3600, 1), 'hours']
        elif exp_time_sec > 60:
            exp_time = [round(exp_time_sec/60, 1), 'mins']
        else:
            exp_time = [round(exp_time_sec), 'sec']
        
        return f"experiment time is approx {exp_time[0]} {exp_time[1]}"

if __name__ == "__main__":

    from newinstruments import demoInstrument

    yoko_ch     = demoInstrument.demoInstrument('GPIB0::7::INSTR', printMessages=False)
    yoko_gt     = demoInstrument.demoInstrument('GPIB0::1::INSTR', printMessages=False)

    lockin_HF   = demoInstrument.demoInstrument('GPIB0::11::INSTR', printMessages=False)
    generator   = demoInstrument.demoInstrument("GPIB::19::INSTR", printMessages=False)

    control_instr_dict = {
                    'Vch': [0, yoko_ch, 'voltage', 'ramp_to_value', 'V'],
                    'Vgt': [0, yoko_gt, 'voltage', 'ramp_to_value', 'V'],
                    'Vac': [0.05, generator, 'voltage', 'ramp_to_value', 'Vpp'],
    }

    readout_instr_dict = {
                        'Vx': [lockin_HF, 'read', 'V'],
                        'Vy': [lockin_HF, 'read', 'V'],
    }

    exp = experiment(control_instr_dict, readout_instr_dict)

    exp.Vac = 200_000_462
    exp.Vch = 0.2
    exp.Vgt =  {'val': 0.2, 'off': 0}
    exp.tconst = 0.05

    exp.comment = f'none'
    exp.comment2 = f'none**2'

    print(tabulate(exp.gettable_ClassAttributes()))

    exp.sweep_params(
        var     =   ['Vch','Vgt'],
        s1      =   0.2,
        s2      =   1.0,
        num     =   51,
        scale   =   'linear',
        offset  =   [0, -1]
    )

    exp.step_params(
        var     =   'Vac',
        s1      =   4_000_000_000,
        s2      =   8_000_000_000,
        num     =   352,
        scale   =   'linear',
        offset  =   0
    )

    print(tabulate(exp.gettable_ClassAttributes()))
    print(exp.estimate_run_time(exp_type='2D'))

    #exp_name = 'test'
    #exp.run(exp_name, exp_type='2D', savedata=True, outerloop=False)
