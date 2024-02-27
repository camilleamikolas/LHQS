from time import sleep
from numpy import random

class demoInstrument():

    def __init__(self, address: str, printMessages: bool):
        self.address = address
        self.printMessages = printMessages

    @property
    def voltage(self) -> float:
        return random.rand()

    @voltage.setter
    def voltage(self, value: float) -> None:
        if self.printMessages:
            print(f'the instrument at address {self.address} is set to {value}')

    def ramp_to_value(self, value: float, duration=0.5):
        self.voltage = value
        sleep(duration)

    @property
    def read(self) -> float:
        return random.rand() + 1.0

if __name__ == "__main__":
    demo = demoInstrument(address='USB_ADDR', printMessages=True)
    demo.voltage = 2.0
    print(demo.voltage)
    print(demo.read)