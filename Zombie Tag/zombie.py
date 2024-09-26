import machine
from machine import Pin,  Timer, PWM
import struct, time, Tufts_ble
from Tufts_ble import Sniff, Yell

class Zombie:
    
    def __init__(self, message):
        self.message = message
        self.buzz = PWM(Pin('GPIO18', Pin.OUT))
        self.buzz.freq(200)
        
        self.zombie_yelling()
        
    def zombie_yelling(self):
        p = Yell()
        while True:
            #message = number
            p.advertise(f'!{int(self.message)}')
            self.buzz.duty_u16(200)
            time.sleep(0.1)
        p.stop_advertising()
