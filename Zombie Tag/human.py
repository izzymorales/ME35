import time, machine, neopixel
from Tufts_ble import Sniff, Yell
from machine import Timer, Pin, PWM

class Human:
    
    def __init__(self, num_zombies):
        # tells if a zombie is in range or not, starts out of range
        self.in_range = [False] * num_zombies  # Track range status for each zombie
        self.timer_running = [False] * num_zombies  # Track timer status for each zombie
        self.timers = [Timer() for _ in range(num_zombies)]  # Create a separate timer for each zombie
        self.not_zombie = True
        self.num_zombies = num_zombies
        
        # Making a lookup table array for zombies, dynamically sized
        self.counter = [0] * self.num_zombies  # One counter for each zombie
        
        #initialize buzzer
        self.buzz = PWM(Pin('GPIO18', Pin.OUT))
        self.buzz.freq(200)
        
        #initialize LEDs
        self.led1 = Pin('GPIO5', Pin.OUT)
        self.led2 = Pin('GPIO4', Pin.OUT)
        self.led1.off()
        self.led2.off()
        
        #initialize neopixel
        self.red = (255,0,0) #red color
        self.green = (0,255,0) #green color
        self.off = (0,0,0)
        self.light = neopixel.NeoPixel(Pin(28),1)
        self.light[0] = self.green
        self.light.write()
        
        #initialize the button
        self.button = Pin('GPIO20', Pin.IN)
        
        #automatically start calling central
        self.central()
        
    # Define a callback function for the timer
    def callback(self, timer, zombie_id):
        m = Yell()
        if self.not_zombie:
            print(f"hit by zombie {zombie_id + 1}!")
            #buzz when hit
            self.buzz.duty_u16(1000)
            time.sleep(0.1)
            self.buzz.duty_u16(0)
            #increase counters
            if self.counter[zombie_id] == 2 and not zombie_id == 4: #we are not allowed to become zombie 5
                print(f"become zombie {zombie_id + 1}")
                self.counter[zombie_id] += 1
                self.not_zombie = False
            else:
                self.counter[zombie_id] += 1
                if self.counter[zombie_id] == 1:
                    #turn on one LED
                    self.led1.on()
                elif self.counter[zombie_id] == 2:
                    #turn on second LED
                    self.led2.on()
                print(self.counter[zombie_id])
            # Stop the timer for this specific zombie
            # self.timer_running[zombie_id] = False
            # m.advertise(f"$${zombie_id +1}:{self.counter[zombie_id]}")
            
    #check if button is pressed to advertise hit array info to computer
    def check_send_array(self):
        if not self.button.value(): #if button is pressed
            m = Yell()
            for i in range(0,self.num_zombies-1):
                for j in range(0,3):
                    m.advertise(f'$${i+1} : {self.counter[i]}')
                    time.sleep(0.1)
                    m.stop_advertising()
            m.stop_advertising()
            self.light[0] = self.off
            self.light.write()
            
    # Start the timer for a specific zombie
    def start_timer(self, zombie_id):
        if self.in_range[zombie_id] and not self.timer_running[zombie_id] and self.not_zombie:
            print(f"timer started for zombie {zombie_id + 1}")
            self.timers[zombie_id].init(period=3000, mode=Timer.ONE_SHOT, callback=lambda t: self.callback(t, zombie_id))  # 3 seconds
            self.timer_running[zombie_id] = True
            
    # Interrupt the timer when out of range for a specific zombie
    def end_timer(self, zombie_id):
        if not self.in_range[zombie_id] and self.timer_running[zombie_id]:
            self.timers[zombie_id].deinit()
            print(f"timer stopped for zombie {zombie_id + 1}")
            self.timer_running[zombie_id] = False
            
    #turn the neopixel green when no zombies in range, and red if any in range
    def scan(self):
        any_in_range = False
        for i in range(self.num_zombies):
            if self.in_range[i]:
                self.light[0] = self.red
                self.light.write()
                any_in_range = True
        if not any_in_range:
            self.light[0] = self.green
            self.light.write()
            
    # Define sniffing for humans
    def central(self):
        c = Sniff('!', verbose=True)
        c.scan(0)  # Scan indefinitely
        while self.not_zombie:  # Loop checking distances while not a zombie
            latest = c.last
            if latest:
                c.last = ''  # Clear the flag for the next advertisement
                rssi = c.get_rssi()
                if rssi > -60:# If within range
                    # Check if the signal is from any zombie
                    for zombie_id in range(self.num_zombies):
                        if latest == f'!{zombie_id + 1}':  # Compare to dynamic zombie IDs
                            self.in_range[zombie_id] = True
                            self.start_timer(zombie_id)
                            print(f"Zombie {zombie_id + 1} detected, RSSI: {rssi}")
                else:
                    for zombie_id in range(self.num_zombies):
                        self.in_range[zombie_id] = False
                        self.end_timer(zombie_id)
            self.scan()
            self.check_send_array()
            time.sleep(0.1)
        # Out of the while loop - become a zombie
        i_am_zombie_id = None
        #loop to find which index is a zombie
        for i in range(self.num_zombies):
            if self.counter[i] == 3:
                i_am_zombie_id = i
        #turn neopixel off
        self.light[0] = self.off
        self.light.write()
        #turn leds off
        self.led1.off()
        self.led2.off()
        self.peripheral(i_am_zombie_id)
        #print('I am a zombie now')
        
    # Define zombie action
    def peripheral(self, zombie_id):
        print("oh hey im a zombie now")
        p = Yell()
        while True:
            p.advertise(f'!{zombie_id+1}') #zombie_id is the array index of the zombie (array is zero indexed)
            self.buzz.duty_u16(200)
            self.check_send_array()
            time.sleep(0.1)
        p.stop_advertising()
