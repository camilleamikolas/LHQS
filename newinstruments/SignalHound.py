import sys
sys.path.append(r'F:\Niyaz\newinstruments\api')

from time import sleep
import sadevice.sa_api as sad

GHz = 1e9
MHz = 1e6
kHz = 1e3

class SignalHoundSA124B():

    def __init__(self, RBW=50e3, VBW=50e3):
        self.handle = sad.sa_open_device()["handle"]
        self.rbw = RBW
        self.vbw = VBW

    def get_spectrum(self, center_freq=4*GHz, span=1*GHz, level=0) -> tuple:
        
        # Configure
        sad.sa_config_center_span(self.handle, center_freq, span)
        sad.sa_config_level(self.handle, level)
        sad.sa_config_sweep_coupling(self.handle, self.rbw, self.vbw, "reject") #was both 250e3
        sad.sa_config_acquisition(self.handle, sad.SA_MIN_MAX, sad.SA_LOG_SCALE)

        # Initialize
        sad.sa_initiate(self.handle, sad.SA_SWEEPING, 0)
        query = sad.sa_query_sweep_info(self.handle)
        sweep_num = query["sweep_length"]
        start_freq = query["start_freq"]
        bin_size = query["bin_size"]
        freqs = [start_freq + i * bin_size for i in range(sweep_num)]

        # Get data
        spectrum = sad.sa_get_sweep_64f(self.handle)["max"]

        return freqs, spectrum

    @property
    def set_freq_for_power(self):
        pass

    @set_freq_for_power.setter
    def set_freq_for_power(self, center_freq=4.0*GHz) -> None:
        span = 250*kHz
        level = 0
        sad.sa_config_center_span(self.handle, center_freq, span)
        sad.sa_config_level(self.handle, level)
        sad.sa_config_sweep_coupling(self.handle, self.rbw, self.vbw, "reject")
        sad.sa_config_acquisition(self.handle, sad.SA_MIN_MAX, sad.SA_LOG_SCALE)
        
        # Initialize
        sad.sa_initiate(self.handle, sad.SA_SWEEPING, 0)

    @property
    def get_power_at_freq(self) -> float:
        # Get data
        spectrum = sad.sa_get_sweep_64f(self.handle)["max"]
        max_power = max(spectrum)
        return max_power
    
    @get_power_at_freq.setter
    def get_power_at_freq(self):
        pass

    def ramp_to_frequency(self, frequency=4.0*GHz, duration=0.5):
        self.set_freq_for_power = frequency
        sleep(duration)

    def close_device(self):
        sad.sa_close_device(self.handle)
        print("Closing Device")

if __name__ == "__main__":
    sadevice = SignalHoundSA124B()
    #f, d = sadevice.get_spectrum(4*GHz, 250*kHz, 0)

    #import matplotlib.pyplot as plt
    #plt.plot(f, d)
    #plt.show()

    sadevice.set_freq_for_power = 4*GHz
    print(sadevice.get_power_at_freq)
    sadevice.close_device()