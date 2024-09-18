import time, mqtt, machine, network, secrets, asyncio, neopixel
from machine import Pin, PWM
from mqtt import MQTTClient
from secrets import mysecrets, nlsecrets

class NightLight:
    
    #INITIALIZE
    def __init__(self):
        self.mqtt_broker = 'broker.hivemq.com' 
        self.port = 1883
        self.topic_sub = nlsecrets['Sub_Topic'] # this reads anything sent to our subscribed topic
        self.buzz = PWM(Pin('GPIO18', Pin.OUT))
        self.buzz.freq(440)
        self.state = (100,0,100)
        self.light = neopixel.NeoPixel(Pin(28),1)
        self.light[0] = self.state
        self.light.write()
        self.led = PWM(Pin('GPIO0', Pin.OUT))
        self.led.freq(50)
        
        
    #WIFI
    def connect(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(mysecrets['SSID'], mysecrets['key'])
        while wlan.ifconfig()[0] == '0.0.0.0':
            print('.', end=' ')
            time.sleep(1)
        # We should have a valid IP now via DHCP
        print(wlan.ifconfig())
        return wlan.ifconfig()
    
    #NEOPIXEL RGB VALUE
    def update_state(self, button_pressed):
        if button_pressed:  # Assuming button_pressed is a boolean
            # Convert tuple to list to modify values
            state_list = list(self.state)
            # Increment each value by 10
            state_list = [(x + 100) if (x + 100) <= 255 else 0 for x in state_list]
            # Convert list back to tuple
            self.state = tuple(state_list)
            self.light[0] = self.state
            self.light.write()
    
    #BUZZER    
    def beep(self, beep_dc):
        # Activate buzzer for 0.5 seconds after button release
        self.buzz.duty_u16(beep_dc)
        time.sleep(0.5)
        self.buzz.duty_u16(0)
        
    #LED
    async def led_breathe(self):
        # Increase brightness from 0 to 65535
        for i in range(0, 65535, 500):
            self.led.duty_u16(i)
            await asyncio.sleep(0.01)
        # Decrease brightness from 65535 to 0
        for i in range(65535, 0, -500):
            self.led.duty_u16(i)
            await asyncio.sleep(0.01)
    
    #MQTT CALLBACK
    def mqtt_connect(self, callback):
        client = MQTTClient('ME35_chris', self.mqtt_broker , self.port, keepalive=60)
        client.connect()
        print('Connected to %s MQTT broker' % (self.mqtt_broker))
        client.set_callback(callback)
        client.subscribe(self.topic_sub)
        return client
    
    #RESET PINS
    def reset(self):
        self.buzz.duty_u16(0) # No beep
        self.light[0] = (0,0,0) # No light
        self.light.write()
        self.led.duty_u16(0)
