import time, mqtt, machine, network, secrets, asyncio, neopixel
from machine import Pin, PWM, I2C, ADC
from mqtt import MQTTClient
from BLE_CEEO import Yell
from secrets import mysecrets, chsecrets
from songlists import pirate_song_me, pirate_song_key

class Drums:
    
    #INITIALIZE
    def __init__(self, scl, sda, scl2, sda2, addr=0x62):
        
        # Songs
        self.pirate_song_me = pirate_song_me
        self.pirate_song_key = pirate_song_key
        
        # I2C stuff for accelerometer
        self.addr = addr
        self.i2c_short = I2C(0, scl=scl, sda=sda, freq=50000)
        self.i2c_tall = I2C(1, scl=scl2, sda=sda2, freq=50000)
        self.init_tap_detection()
        
        # Photoresistor setup
        self.photo_pin = ADC(Pin(28))
        
        # Button setup for bass and keyboard
        self.bass_btn = Pin('GPIO17', Pin.IN, Pin.PULL_UP)
        self.keyb_btn = Pin('GPIO16', Pin.IN, Pin.PULL_UP)
        
        # Motor setup
        self.Ma = PWM(Pin('GPIO18', Pin.OUT))
        self.Ma.freq(100)
        self.Ma.duty_u16(0)
        self.Mb = PWM(Pin('GPIO19', Pin.OUT))
        self.Mb.freq(100)
        self.Mb.duty_u16(0)
        
        # MQTT setup
        self.mqtt_broker = 'broker.hivemq.com' 
        self.port = 1883
        self.topic_sub = chsecrets['Sub_Topic'] # this reads anything sent to our subscribed topic
        self.topic_pub = chsecrets['Pub_Topic']
        
        # Connect to wifi and MQTT
        self.connect()
        self.mqtt_connect()
        
        # Connect w/ MIDI
        self.midi_connect()
        
        # Run tasks
        drum_msg = 'drums'
        self.client.publish(self.topic_pub, drum_msg)
        asyncio.run(self.main())
        
    #ACCELEROMETER SETUP
    def write_byte_short(self, reg, value):
        self.i2c_short.writeto_mem(self.addr, reg, value.to_bytes(1, 'little'))
        
    def write_byte_tall(self, reg, value):
        self.i2c_tall.writeto_mem(self.addr, reg, value.to_bytes(1, 'little'))

    def read_byte_short(self, reg):
        try:
            return int.from_bytes(self.i2c_short.readfrom_mem(self.addr, reg, 1), 'little')
        except OSError as e:
            print("I2C read error short:", e)
            return None  # Return a default or error value

    
    def read_byte_tall(self, reg):
        try:
            return int.from_bytes(self.i2c_tall.readfrom_mem(self.addr, reg, 1), 'little')
        except OSError as e:
            print("I2C read error:", e)
            return None  # Return a default or error value

    def init_tap_detection(self):
        # Enable single (bit 5) and double (bit 4) tap interrupts
        tap_interrupt = (1 << 5) | (1 << 4)  # Puts a 1 at bit 5 and a 1 at bit 4
        self.write_byte_short(0x16, tap_interrupt)
        self.write_byte_tall(0x16, tap_interrupt)
        # Re-check if bits 5 and 4 are set in register 0x16
        int_config_short = self.read_byte_short(0x16)
        int_config_tall = self.read_byte_tall(0x16)
        print(f"Interrupt config (0x16): {int_config_short:08b}")  # Should print 00110000
        print(f"Interrupt config (0x16): {int_config_tall:08b}")  # Should print 00110000

        self.write_byte_short(0x10, 0x03)  # Set ODR to 250Hz
        self.write_byte_short(0x11, 0x02)  # Set to normal mode
        self.write_byte_tall(0x10, 0x03)  # Set ODR to 250Hz
        self.write_byte_tall(0x11, 0x02)  # Set to normal mode
        
        # Set tap threshold (e.g., 250 mg in 8g range, value = 4 in 8g mode, adjust as necessary)
        self.write_byte_short(0x0F, 0x00)  # Set to 2g mode
        self.write_byte_short(0x2B, 0x03)  # Lower threshold for 2g mode
        self.write_byte_tall(0x0F, 0x00)  # Set to 2g mode
        self.write_byte_tall(0x2B, 0x03)  # Lower threshold for 2g mode

        # Set tap parameters: TAP_DUR (bits 0-2), TAP_SHOCK (bit 6), TAP_QUIET (bit 7) in register 0x2A
        tap_dur = 0x07  # Big value for tap duration
        tap_shock = 0x01  # Low value for shock
        tap_quiet = 0x01  # Low value for quiet
        tap_settings = (tap_quiet << 7) | (tap_shock << 6) | tap_dur
        self.write_byte_short(0x2A, tap_settings)
        self.write_byte_tall(0x2A, tap_settings)
    
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
            decoded_msg = msg.decode()
            if decoded_msg.isdigit():
                numeric_value = int(decoded_msg)
                self.potent = numeric_value
            print((topic.decode(), msg.decode()))
        self.client = MQTTClient('Drumsah', self.mqtt_broker , self.port, keepalive=60)
        self.client.connect()
        print('Connected to %s MQTT broker' % (self.mqtt_broker))
        self.client.set_callback(callback)
        self.client.subscribe(self.topic_sub)
        
    # GARAGEBAND STUFF
    def midi_connect(self):
        self.NoteOn = 0x90
        self.NoteOff = 0x80
        self.StopNotes = 123
        #self.SetInstroment = 0xC0
        self.Reset = 0xFF

        self.velocity = {'off':0, 'pppp':8,'ppp':20,'pp':31,'p':42,'mp':53,
            'mf':64,'f':80,'ff':96,'fff':112,'ffff':127}
            
        self.p = Yell('Izzy', verbose = True, type = 'midi')
        self.p.connect_up()
        
        self.channel = 9
        self.note_short = 50
        self.note_tall = 35
        self.note_bass = 36
        self.note_cymbal = 49
        self.cmd = self.NoteOn

        self.channel = 0x0F & self.channel
        self.timestamp_ms = time.ticks_ms()
        self.tsM = (self.timestamp_ms >> 7 & 0b111111) | 0x80
        self.tsL =  0x80 | (self.timestamp_ms & 0b1111111)
        self.c =  self.cmd | self.channel     
#         self.payload_short = bytes([self.tsM,self.tsL,self.c,self.note_short,self.velocity['f']])
#         self.payload_tall = bytes([self.tsM,self.tsL,self.c,self.note_tall,self.velocity['f']])
#         self.payload_bass = bytes([self.tsM,self.tsL,self.c,self.note_bass,self.velocity['f']])
#         self.payload_cymbal = bytes([self.tsM,self.tsL,self.c,self.note_cymbal,self.velocity['f']])
    
    def play_note(self, on, note, velocity):
        cmd_line = on | self.channel 
        self.payload = bytes([self.tsM,self.tsL,cmd_line,note,velocity])
        self.p.send(self.payload)
        
        
    #ASYNC STUFF 
    async def check_mqtt(self):
        while True:
            self.client.check_msg()
            await asyncio.sleep(0.1)
            
    async def check_tap_status(self): 
        while True:
            # Check the interrupt status register for single and double tap (register 0x09)
            status_short = self.read_byte_short(0x09)
            single_tap_short = status_short & 0x20  # Bit 5 for single tap
            double_tap_short = status_short & 0x10  # Bit 4 for double tap
            status_tall = self.read_byte_tall(0x09)
            single_tap_tall = status_tall & 0x20  # Bit 5 for single tap
            double_tap_tall = status_tall & 0x10  # Bit 4 for double tap
            
            # add code below for changing speed with TM and changing volume with potentiometer
            
            if single_tap_short:
                print("Single tap (short) detected!")
                self.volume = int((self.potent / 4095) * 127)
                self.payload_short = bytes([self.tsM,self.tsL,self.c,self.note_short,self.volume])
                self.p.send(self.payload_short)
            if single_tap_tall:
                print("Single tap (tall) detected!")
                self.volume = int((self.potent / 4095) * 127)
                self.payload_tall = bytes([self.tsM,self.tsL,self.c,self.note_tall,self.volume])
                self.p.send(self.payload_tall)
            if single_tap_short and single_tap_tall:
                print('Both detected!')
                self.volume = int((self.potent / 4095) * 127)
                self.payload_short = bytes([self.tsM,self.tsL,self.c,self.note_short,self.volume])
                self.payload_tall = bytes([self.tsM,self.tsL,self.c,self.note_tall,self.volume])
                self.p.send(self.payload_short)
                self.p.send(self.payload_tall)
            if double_tap_tall:
                print("Double tap detected!")
                elapsed_time = 0.0
                drum_msg = 'pirate'
                
                self.client.publish(self.topic_pub, drum_msg)
                self.vol = self.potent
                for event in self.pirate_song_me: # loop through the MIDI notes and pauses when photoresistor is covered
                    light_value = self.photo_pin.read_u16()  # read analog value (0-65535)
                    time_to_wait = event['time'] - elapsed_time # calculate the time to wait based on the event's timestamp
                    if time_to_wait > 0:
                        await asyncio.sleep(time_to_wait)
                    while light_value <= 5000:
                        self.Ma.duty_u16(0)
                        light_value = self.photo_pin.read_u16()
                        await asyncio.sleep(0.01)
                    if event['type'] == 'note_on':
                        prev_vol = self.vol
                        self.vol = self.potent
                        self.diff = self.vol - prev_vol
                        adjusted_vel = int(max(0, min(127, event['velocity'] + pot_change * 127 / 4095)))
                        self.play_note(self.NoteOn, event['note'], adjusted_vel)
                        self.Ma.duty_u16(50000)
                    elif event['type'] == 'note_off':
                        self.play_note(self.NoteOff, event['note'], 0)  # velocity is 0
                        self.Ma.duty_u16(0)
                    elapsed_time = event['time'] # update the elapsed time
                    
                self.Ma.duty_u16(0)            
                await asyncio.sleep(0.01)
                drum_msg = 'drums'
                self.client.publish(self.topic_pub, drum_msg)
                
            await asyncio.sleep(0.01)
            
    async def check_bass(self):
        previous_btn_state = self.bass_btn.value()  # initialize with the current state
        while True:
            current_btn_state = self.bass_btn.value()
            if previous_btn_state == 0 and current_btn_state == 1:  # button was pressed (0) and is now released (1)
                #print('button released!')
                self.volume = int((self.potent / 4095) * 127)
                self.payload_bass = bytes([self.tsM,self.tsL,self.c,self.note_bass,self.volume])
                self.payload_cymbal = bytes([self.tsM,self.tsL,self.c,self.note_cymbal,self.volume])
                self.p.send(self.payload_bass)
                self.p.send(self.payload_cymbal)
            previous_btn_state = current_btn_state # update for next loop
            await asyncio.sleep(0.01)  # delay for button debouncing
        
    async def check_keyb(self):
        previous_btn_state = self.keyb_btn.value()  # initialize with the current state
        while True:
            current_btn_state = self.keyb_btn.value()
            if previous_btn_state == 0 and current_btn_state == 1:  # button was pressed (0) and is now released (1)
                print('key!')
                self.p.disconnect()
                await asyncio.sleep(0.5)
                self.p.connect_up()
                elapsed_time = 0.0
                
                # add code for sending mqtt message when song is being played, and another one when song stops
                   
                for event in self.pirate_song_key: # loop through the MIDI notes and pauses when photoresistor is covered
                    light_value = self.photo_pin.read_u16()  # read analog value (0-65535)
                    time_to_wait = event['time'] - elapsed_time # calculate the time to wait based on the event's timestamp
                    if time_to_wait > 0:
                        await asyncio.sleep(time_to_wait)
                    while light_value <= 5000:
                        self.Ma.duty_u16(0)
                        light_value = self.photo_pin.read_u16()
                        await asyncio.sleep(0.01)
                    if event['type'] == 'note_on':
                        prev_vol = self.vol
                        self.vol = self.potent
                        self.diff = self.vol - prev_vol
                        adjusted_vel = int(max(0, min(127, event['velocity'] + pot_change * 127 / 4095)))
                        self.play_note(self.NoteOn, event['note'], adjusted_vel)
                        self.Ma.duty_u16(50000)
                    elif event['type'] == 'note_off':
                        self.play_note(self.NoteOff, event['note'], 0)  # velocity is 0
                        self.Ma.duty_u16(0)
                    elapsed_time = event['time'] # update the elapsed time
                            
                await asyncio.sleep(0.01)
                
            previous_btn_state = current_btn_state # update for next loop
            await asyncio.sleep(0.01)  # delay for button debouncing
        
            
    async def main(self):
        self.go = False
        tasks = asyncio.gather(self.check_mqtt(),self.check_tap_status(),self.check_bass(),self.check_keyb())
        await tasks # wait for duration

        
# Main code!
scl = Pin('GPIO5', Pin.OUT)
sda = Pin('GPIO4', Pin.OUT)
scl2 = Pin('GPIO27', Pin.OUT)
sda2 = Pin('GPIO26', Pin.OUT)

boom = Drums(scl, sda, scl2, sda2)
