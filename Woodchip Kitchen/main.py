# Python
import time
import asyncio
import random
# MicroPython
from machine import Pin, PWM, UART                  # type: ignore (suppresses Pylance lint warning)
# custom
from BLE_CEEO import Yell, Listen                   # type: ignore
from espnow_bluetooth_relay import check_bluetooth
from buttonsequences import ButtonSequenceManager

threadsleep = 0.01

class Woodchip_Kitchen:
    
    def __init__(self):
        
        # Need to add stuff for on/off switch, apriltag separation, arrow stepper motor setup, etc.
        self.on_switch = Pin('GPIO8', Pin.IN, Pin.PULL_UP)
        self.on = not bool(self.on_switch.value()) # the switch is connected to ground when the game is on

        self.mode_switch = Pin('GPIO9', Pin.IN, Pin.PULL_UP)
        self.local_mode = bool(self.mode_switch.value()) # the switch is connected to ground when the game is in global mode, add if statements in main


        # Button setup
#         self.btn1 = Pin('GPIO0', Pin.IN, Pin.PULL_UP) # pull up resistor; other btn rail is connected to ground, so btn.value becomes 0 when pressed
#         self.btn2 = Pin('GPIO1', Pin.IN, Pin.PULL_UP)
#         self.btn3 = Pin('GPIO2', Pin.IN, Pin.PULL_UP)
#         self.btn4 = Pin('GPIO3', Pin.IN, Pin.PULL_UP)
        
        # Button LED setup
#         self.led1 = Pin('GPIO4', Pin.OUT) 
#         self.led2 = Pin('GPIO5', Pin.OUT)
#         self.led3 = Pin('GPIO6', Pin.OUT)
#         self.led4 = Pin('GPIO7', Pin.OUT)
        
        self.button_sequence_manager = ButtonSequenceManager()

        # More LED setup
        # for status leds on station?
        
        # Stepper motor setup
        self.in1 = Pin('GPIO16', Pin.OUT)
        self.in2 = Pin('GPIO17', Pin.OUT)
        self.in3 = Pin('GPIO18', Pin.OUT)
        self.in4 = Pin('GPIO19', Pin.OUT)
        
        self.in1_arrow = Pin('GPIO15', Pin.OUT)
        self.in2_arrow = Pin('GPIO14', Pin.OUT)
        self.in3_arrow = Pin('GPIO13', Pin.OUT)
        self.in4_arrow = Pin('GPIO12', Pin.OUT)
        
        # Forward step sequence
        self.forward_step_sequence = [
            [1, 0, 0, 0],  # Step 1
            [1, 1, 0, 0],  # Step 2
            [0, 1, 0, 0],  # Step 3
            [0, 1, 1, 0],  # Step 4
            [0, 0, 1, 0],  # Step 5
            [0, 0, 1, 1],  # Step 6
            [0, 0, 0, 1],  # Step 7
            [1, 0, 0, 1],  # Step 8
        ]

        # Reverse step sequence
        self.reverse_step_sequence = [
            [1, 0, 0, 1],  # Step 8 
            [0, 0, 0, 1],  # Step 7
            [0, 0, 1, 1],  # Step 6
            [0, 0, 1, 0],  # Step 5
            [0, 1, 1, 0],  # Step 4
            [0, 1, 0, 0],  # Step 3
            [1, 1, 0, 0],  # Step 2
            [1, 0, 0, 0],  # Step 1 
        ]
        
        # Food option setup
        self.food_functions = {
            "burger": self.burger,
            "smoothie": self.smoothie,
            "ramen": self.ramen
        }
        self.food_steps = {
            "burger": 128, 
            "smoothie": 256,
            "ramen": 384
        }
        self.food_steps_arrow = {
            "burger": 128, 
            "smoothie": 192,
            "ramen": 256
        }
        self.foods = ['burger', 'smoothie', 'ramen']
        

        
        
    # Function to set the stepper motor states
    def set_step(self, step, in1, in2, in3, in4):
        in1.value(step[0])
        in2.value(step[1])
        in3.value(step[2])
        in4.value(step[3])

    # Function to rotate the stepper motors (pass the step sequence)
    def rotate_motor(self, delay, steps, step_sequence, in1, in2, in3, in4):
        print('rotating ahhhhh')
        for _ in range(steps):
            for step in step_sequence:
                self.set_step(step, in1, in2, in3, in4)
                time.sleep(delay)
                
    def generate_random_tuple(self,length):

        if length < 3:
            raise ValueError("Length must be at least 3 to accommodate a nested tuple.")
        
        # Create the nested tuple with distinct numbers
        first_number = random.choice([1, 2, 3, 4])
        second_number = random.choice([num for num in [1, 2, 3, 4] if num != first_number])
        nested_tuple = (first_number, second_number)
        
        # Initialize the main tuple list
        main_numbers = []
        
        # Fill the rest of the tuple ensuring no consecutive repeats
        while len(main_numbers) < length - 1:
            next_number = random.choice([1, 2, 3, 4])
            if not main_numbers or main_numbers[-1] != next_number:
                main_numbers.append(next_number)
        
        # Insert the nested tuple at a random position ensuring no consecutive repeats
        insert_index = random.randint(0, length - 2)
        if insert_index > 0 and main_numbers[insert_index - 1] == nested_tuple[0]:
            # Adjust if the first number of the nested tuple would repeat
            nested_tuple = (random.choice([num for num in [1, 2, 3, 4] if num != main_numbers[insert_index - 1]]), nested_tuple[1])
        if insert_index < length - 2 and main_numbers[insert_index] == nested_tuple[1]:
            # Adjust if the second number of the nested tuple would repeat
            nested_tuple = (nested_tuple[0], random.choice([num for num in [1, 2, 3, 4] if num != main_numbers[insert_index]]))
        
        main_numbers.insert(insert_index, nested_tuple)
        return tuple(main_numbers)
                
    # Functions for each food sequence
    def burger(self):
        tuple_length = 6 
        randomized_tuple = self.generate_random_tuple(tuple_length)
        message = 'burger'
        self.rotate_motor(0.001, self.food_steps_arrow[message], self.forward_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow) # arrow motors
        self.rotate_motor(0.001, self.food_steps[message], self.forward_step_sequence, self.in1, self.in2, self.in3, self.in4) # board motors
        self.button_sequence_manager.new_sequence((4,randomized_tuple[0],randomized_tuple[1],randomized_tuple[2],randomized_tuple[3],randomized_tuple[4],randomized_tuple[5],4))
        while not self.button_sequence_manager.sequence_complete:
            time.sleep(0.1)
        self.rotate_motor(0.001, self.food_steps[message], self.reverse_step_sequence, self.in1, self.in2, self.in3, self.in4)
        self.rotate_motor(0.001, self.food_steps_arrow[message], self.reverse_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow)

    def smoothie(self):
        tuple_length = 8 
        randomized_tuple = self.generate_random_tuple(tuple_length)
        message = 'smoothie'
        self.rotate_motor(0.001, self.food_steps_arrow[message], self.forward_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow) # arrow motors
        self.rotate_motor(0.001, self.food_steps[message], self.forward_step_sequence, self.in1, self.in2, self.in3, self.in4) # board motors
        self.button_sequence_manager.new_sequence((randomized_tuple[0],randomized_tuple[1],randomized_tuple[2],randomized_tuple[3],randomized_tuple[4],randomized_tuple[5],randomized_tuple[6],randomized_tuple[7]))
        while not self.button_sequence_manager.sequence_complete:
            time.sleep(0.1)
        self.rotate_motor(0.001, self.food_steps[message], self.reverse_step_sequence, self.in1, self.in2, self.in3, self.in4)
        self.rotate_motor(0.001, self.food_steps_arrow[message], self.reverse_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow)
        
    def ramen(self):
        tuple_length = 8 
        randomized_tuple = self.generate_random_tuple(tuple_length)
        message = 'ramen'
        self.rotate_motor(0.001, self.food_steps_arrow[message], self.forward_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow) # arrow motors
        self.rotate_motor(0.001, self.food_steps[message], self.forward_step_sequence, self.in1, self.in2, self.in3, self.in4) # board motors
        self.button_sequence_manager.new_sequence((randomized_tuple[0],randomized_tuple[1],randomized_tuple[2],randomized_tuple[3],randomized_tuple[4],randomized_tuple[5],randomized_tuple[6],randomized_tuple[7]))
        while not self.button_sequence_manager.sequence_complete:
            time.sleep(0.1)
        self.rotate_motor(0.001, self.food_steps[message], self.reverse_step_sequence, self.in1, self.in2, self.in3, self.in4)
        self.rotate_motor(0.001, self.food_steps_arrow[message], self.reverse_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow)
    
    # Monitoring functions, async
    async def monitor_switches(self):
        while True:
            self.on = not bool(self.on_switch.value())
            self.local_mode = bool(self.mode_switch.value())
            await asyncio.sleep(threadsleep)
    
        
    # Game code, async
    async def game(self):
        while True:
            if self.on:
                print('self.local_mode: {}'.format(self.local_mode))
                if self.local_mode:
                    message = random.choice(self.foods)
                else:
                    message = check_bluetooth()
                    print('received {} over bluetooth'.format(message))
                    if message == 'k0': message = 'burger'
                    if message == 'k1': message = 'smoothie'
                    if message == 'k2': message = 'ramen'
                
                if message in self.food_functions:
                    print(message)
                    # rotate motors to correct food position
                    #self.rotate_motor(0.001, self.food_steps_arrow[message], self.forward_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow) # arrow motors
                    #self.rotate_motor(0.001, self.food_steps[message], self.forward_step_sequence, self.in1, self.in2, self.in3, self.in4) # board motors
                    self.food_functions[message]()  # Execute the corresponding function
                    print('game!')
                    # rotate motor back to starting position
                    #self.rotate_motor(0.001, self.food_steps[message], self.reverse_step_sequence, self.in1, self.in2, self.in3, self.in4)
                    #self.rotate_motor(0.001, self.food_steps_arrow[message], self.reverse_step_sequence, self.in1_arrow, self.in2_arrow, self.in3_arrow, self.in4_arrow)
                    await asyncio.sleep(1)
                else:
                    print("No order received.")
            await asyncio.sleep(0.01)  
            
    # Main code!
    async def main(self):
        tasks = asyncio.gather(self.monitor_switches(),self.game())
        await tasks # wait for duration



if __name__ == '__main__':
    kitchen = Woodchip_Kitchen()
    asyncio.run(kitchen.main())
