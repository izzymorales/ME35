import time, mqtt, machine, network, secrets, asyncio, neopixel, framebuf, ssd1306
from machine import Pin, PWM, SoftI2C, ADC
from mqtt import MQTTClient
from secrets import mysecrets, chsecrets
from storage import bitmap

class DrumDisplay:
    
    #INITIALIZE
    def __init__(self): 
        
        # Setting up screen
        self.i2c = SoftI2C(scl = Pin(7), sda = Pin(6))
        self.screen = ssd1306.SSD1306_I2C(128,64,self.i2c)
        self.bitmap = bitmap
        self.fbuf = framebuf.FrameBuffer(self.bitmap, 128, 64, framebuf.MONO_HLSB)
        
        # Setting up potentiometer
        self.pot = ADC(Pin(3))
        self.pot.atten(ADC.ATTN_11DB) # the pin expects a voltage range up to 3.3V
        #print(pot.read()) #range 0-4095
        
        
        # MQTT setup
        self.mqtt_broker = 'broker.hivemq.com' 
        self.port = 1883
        self.topic_sub = chsecrets['Sub_Topic'] # this reads anything sent to our subscribed topic
        self.topic_pub = chsecrets['Pub_Topic']
        
        # Connect to wifi and MQTT
        self.connect()
        self.mqtt_connect()
        
        # Run tasks
        self.display_changed = False
        self.drum = True
        self.pirate = False
        self.key = False
        self.previous_pot_value = 0
        
        asyncio.run(self.main())
        
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
    
    #MQTT CALLBACK
    def mqtt_connect(self):
        def callback(topic, msg):
            if (msg.decode()) == 'drums':
                self.key = False
                self.pirate = False
                self.drum = True
            elif (msg.decode()) == 'pirate':
                self.drum = False
                self.key = False
                self.pirate = True
            elif (msg.decode()) == 'key':
                self.drum = False
                self.pirate = False
                self.key = True
            self.display_changed = True
            print((topic.decode(), msg.decode()))
        self.client = MQTTClient('Drumsyay', self.mqtt_broker , self.port, keepalive=60)
        self.client.connect()
        print('Connected to %s MQTT broker' % (self.mqtt_broker))
        self.client.set_callback(callback)
        self.client.subscribe(self.topic_sub)
        
    #ASYNC STUFF (or callback unsure)
    async def check_mqtt(self):
        while True:
            self.client.check_msg()
            await asyncio.sleep(0.1)
            
    async def check_potentiometer(self):
        while True:
            current_value = self.pot.read()
            if abs(current_value - self.previous_pot_value) >= 20:
                self.previous_pot_value = current_value
                print(f"Potentiometer changed: {current_value}")
                self.client.publish(self.topic_pub, str(current_value)) # publish the new potentiometer value to MQTT
            await asyncio.sleep(0.1)
        
    async def display_screen(self):
        
        while True:
            if self.display_changed:
                self.screen.fill(0)
                if self.drum:
                    self.screen.fill(0)
                    self.screen.blit(self.fbuf, 0, 0)
                elif self.pirate:
                    self.screen.fill(0)
                    self.screen.text('Playing:', 0, 0, 1)  # Display "Playing:" at the top (0,0)
                    self.screen.text('Pirates of the', 0, 10, 1)  
                    self.screen.text('Caribbean Theme', 0, 20, 1)  
                    self.screen.text('Song (Drums)', 0, 30, 1)
                elif self.key:
                    self.screen.fill(0)
                    self.screen.text('Playing:', 0, 0, 1)  # Display "Playing:" at the top (0,0)
                    self.screen.text('Pirates of the', 0, 10, 1) 
                    self.screen.text('Caribbean Theme', 0, 20, 1)  
                    self.screen.text('Song (Keyboard)', 0, 30, 1)
                self.screen.show()
                self.display_changed = False
            await asyncio.sleep(0.01)
            
    async def main(self):
        tasks = asyncio.gather(self.check_mqtt(),self.check_potentiometer(),self.display_screen())
        await tasks # wait for duration
        
woo = DrumDisplay()
