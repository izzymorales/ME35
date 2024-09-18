import time, mqtt, machine, network, secrets, asyncio, neopixel
from machine import Pin, PWM, I2C
from mqtt import MQTTClient
from secrets import mysecrets, nlsecrets

class NightLight:
    
    #INITIALIZE
    def __init__(self, scl, sda, addr=0x62):
        
        # I2C stuff for accelerometer
        self.addr = addr
        self.i2c = I2C(0, scl=scl, sda=sda, freq=100000)
        self.init_tap_detection()
        
        # MQTT setup
        self.mqtt_broker = 'broker.hivemq.com' 
        self.port = 1883
        self.topic_sub = nlsecrets['Sub_Topic'] # this reads anything sent to our subscribed topic
        self.topic_pub = 'ME35-24/collab'
        self.msg = 'hello world'
        
        # Buzzer setup
        self.buzz = PWM(Pin('GPIO18', Pin.OUT))
        self.buzz.freq(440)
        
        # Song setup
        # Define the frequency for each note (in Hz)
        self.notes = {
            'C4': 261,
            'D4': 294,
            'E4': 329,
            'F4': 349,
            'G4': 392,
            'A4': 440,
            'B4': 493,
            'C5': 523,
            'REST': 0
        }

        # Define a short song (each tuple is (note, duration in seconds))
        self.song = [
            ('C4', 0.4),
            ('D4', 0.4),
            ('E4', 0.4),
            ('F4', 0.4),
            ('G4', 0.4),
            ('A4', 0.4),
            ('B4', 0.4),
            ('C5', 0.4),
            ('REST', 0.2)
        ]
        
        # Neopixel setup
        self.state = (204,85,0)
        self.light = neopixel.NeoPixel(Pin(28),1)
        self.light[0] = self.state
        self.light.write()
        
        # Breathing LED setup
        self.led = PWM(Pin('GPIO0', Pin.OUT))
        self.led.freq(50)
        
        # External LEDs
        self.light1 = Pin('GPIO8', Pin.OUT)
        self.light2 = Pin('GPIO9', Pin.OUT)
        self.light1.off()
        self.light2.off()
        self.led_status = False
        
        # Connect to wifi and MQTT
        self.connect()
        self.mqtt_connect()
        
        # Run tasks
        asyncio.run(self.main())
        
    #ACCELEROMETER SETUP
    def write_byte(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, value.to_bytes(1, 'little'))

    def read_byte(self, reg):
        return int.from_bytes(self.i2c.readfrom_mem(self.addr, reg, 1), 'little')

    def init_tap_detection(self):
        # Enable single (bit 5) and double (bit 4) tap interrupts
        tap_interrupt = (1 << 5) | (1 << 4)  # Puts a 1 at bit 5 and a 1 at bit 4
        self.write_byte(0x16, tap_interrupt)
        # Re-check if bits 5 and 4 are set in register 0x16
        int_config = self.read_byte(0x16)
        print(f"Interrupt config (0x16): {int_config:08b}")  # Should print 00110000

        self.write_byte(0x10, 0x03)  # Set ODR to 250Hz
        self.write_byte(0x11, 0x02)  # Set to normal mode
        
        # Set tap threshold (e.g., 250 mg in 8g range, value = 4 in 8g mode, adjust as necessary)
        self.write_byte(0x0F, 0x00)  # Set to 2g mode
        self.write_byte(0x2B, 0x03)  # Lower threshold for 2g mode

        # Set tap parameters: TAP_DUR (bits 0-2), TAP_SHOCK (bit 6), TAP_QUIET (bit 7) in register 0x2A
        tap_dur = 0x07  # Big value for tap duration
        tap_shock = 0x01  # Low value for shock
        tap_quiet = 0x01  # Low value for quiet
        tap_settings = (tap_quiet << 7) | (tap_shock << 6) | tap_dur
        self.write_byte(0x2A, tap_settings)

    async def check_tap_status(self):
        while True:
            if self.go:
                # Check the interrupt status register for single and double tap (register 0x09)
                status = self.read_byte(0x09)
                single_tap = status & 0x20  # Bit 5 for single tap
                double_tap = status & 0x10  # Bit 4 for double tap
                if single_tap:
                    print("Single tap detected!")
                    self.update_state(True) # Update state and NeoPixel light after single tap
                if double_tap:
                    print("Double tap detected!")
                    self.play_song()
                    self.client.publish(self.topic_pub, self.msg)
                await asyncio.sleep(0.01)
            if not self.go:
                self.reset()
                await asyncio.sleep(0.01)
    
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
        
    def play_song(self):
        for note, duration in self.song:
            freq = self.notes[note]
            if freq == 0:
                self.buzz.duty_u16(0)  # No sound for rest
            else:
                self.buzz.freq(freq)
                self.buzz.duty_u16(1000)  # Adjust volume (0-65535)
            time.sleep(duration)
            self.buzz.duty_u16(0)  # Stop sound between notes
            time.sleep(0.05)  # Short pause between notes
    
    #MQTT CALLBACK
    def mqtt_connect(self):
        def callback(topic, msg):
            if (msg.decode()) == 'Go':
                self.go = True
                print('Activated!')
            elif (msg.decode()) == 'Stop':
                self.go = False
                print('Off!')
            print((topic.decode(), msg.decode()))
        self.client = MQTTClient('ME35_chris', self.mqtt_broker , self.port, keepalive=60)
        self.client.connect()
        print('Connected to %s MQTT broker' % (self.mqtt_broker))
        self.client.set_callback(callback)
        self.client.subscribe(self.topic_sub)
    
    #RESET PINS
    def reset(self):
        self.buzz.duty_u16(0) # No beep
        self.light[0] = (0,0,0) # No light
        self.light.write()
        self.led.duty_u16(0)
        self.light1.off()
        self.light2.off()
    
    #ASYNC STUFF
    async def check_mqtt(self):
        while True:
            self.client.check_msg()
            await asyncio.sleep(0.1)
            
    async def breathe(self):
        while True:
            if self.go:
                # Increase brightness from 0 to 65535
                for i in range(0, 65535, 500):
                    self.led.duty_u16(i)
                    await asyncio.sleep(0.01)
                # Decrease brightness from 65535 to 0
                for i in range(65535, 0, -500):
                    self.led.duty_u16(i)
                    await asyncio.sleep(0.01)
            if not self.go:
                self.reset()
                await asyncio.sleep(0.01)
                
    async def check_btn(self):
        btn = Pin('GPIO22', Pin.IN, Pin.PULL_DOWN) #22 for ext btn
        previous_btn_state = btn.value()
        while True: 
            if self.go:
                current_btn_state = btn.value()
                if previous_btn_state == False and current_btn_state == True: # Button was pressed and is now released
                    print('button released!')
                    self.beep(1000) # beep
                    if self.led_status == False:  # Turn off if on
                        self.light1.on()
                        self.light2.on()
                        self.led_status = True
                    else: # Turn on if off
                        self.light1.off()
                        self.light2.off()
                        self.led_status = False

                    time.sleep(0.1)  # Small delay to debounce
                previous_btn_state = current_btn_state # Update the previous button state for the next loop
                await asyncio.sleep(0.01) # Small delay to avoid busy-waiting
            if not self.go:
                self.reset()
                await asyncio.sleep(0.01)
                
    async def main(self):
        self.go = False
        tasks = asyncio.gather(self.check_mqtt(),self.check_btn(),self.breathe(),self.check_tap_status())
        await tasks # wait for duration

        
# Main code!
scl = Pin('GPIO5', Pin.OUT)
sda = Pin('GPIO4', Pin.OUT)

nl = NightLight(scl, sda)
