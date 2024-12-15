from machine import Pin
import time

class ButtonSequenceManager:
    """Manages a sequence-based button game using GPIO pins."""
    
    BUTTON_CONFIG = {
        1: {"button_pin": "GPIO0", "led_pin": "GPIO4"},
        2: {"button_pin": "GPIO1", "led_pin": "GPIO5"},
        3: {"button_pin": "GPIO2", "led_pin": "GPIO6"},
        4: {"button_pin": "GPIO3", "led_pin": "GPIO7"},
    }
    DEBOUNCE_MS = 50  # Debounce time in milliseconds
    TIME_WINDOW_MS = 500  # Time window for multi-button presses

    def __init__(self):
        self.buttons = {}
        self.current_sequence = []
        self.current_index = 0
        self.last_time = 0
        self.last_pressed = {1: 0, 2: 0, 3: 0, 4: 0}  # Track last press time for each button
        self.sequence_complete = True

        # Initialize button handlers and their LEDs
        for button_id, config in self.BUTTON_CONFIG.items():
            self.buttons[button_id] = {
                "button": Pin(config["button_pin"], Pin.IN, Pin.PULL_UP),
                "led": Pin(config["led_pin"], Pin.OUT)
            }
            # Attach interrupt handlers
            self.buttons[button_id]["button"].irq(
                trigger=Pin.IRQ_RISING,  # Trigger on button release
                handler=lambda pin, b_id=button_id: self._button_callback(b_id)
            )

    def new_sequence(self, sequence):
        self.sequence_complete = False
        self.current_sequence = sequence
        self.current_index = 0
        self._reset_leds()
        self._activate_current_step()

    def _activate_current_step(self):
        if self.current_index < len(self.current_sequence):
            current_step = self.current_sequence[self.current_index]
            if isinstance(current_step, int):
                self.buttons[current_step]["led"].on()
            elif isinstance(current_step, tuple):
                for button_id in current_step:
                    self.buttons[button_id]["led"].on()

    def _deactivate_leds(self, button_ids):
        if isinstance(button_ids, int):
            self.buttons[button_ids]["led"].off()
        elif isinstance(button_ids, tuple):
            for button_id in button_ids:
                self.buttons[button_id]["led"].off()

    def _reset_leds(self):
        for config in self.BUTTON_CONFIG.values():
            Pin(config["led_pin"], Pin.OUT).off()

    def _button_callback(self, button_id):
        current_time = time.ticks_ms()

        # Debounce check
        if time.ticks_diff(current_time, self.last_time) < self.DEBOUNCE_MS:
            return
        self.last_time = current_time

        # Update the last pressed time for this button
        self.last_pressed[button_id] = current_time

        # Check the current step in the sequence
        if self.current_index >= len(self.current_sequence):
            return

        current_step = self.current_sequence[self.current_index]

        if isinstance(current_step, int) and button_id == current_step:
            # Single button press matches
            print(f"Button {button_id} pressed correctly!")
            self._deactivate_leds(current_step)
            self._advance_sequence()
        elif isinstance(current_step, tuple):
            # Multi-button press validation
            if self._all_buttons_pressed(current_step):
                print(f"Buttons {current_step} pressed correctly!")
                self._deactivate_leds(current_step)
                self._advance_sequence()

    def _all_buttons_pressed(self, button_ids):
        """
        Check if all buttons in a tuple were pressed within the time window.
        """
        current_time = time.ticks_ms()
        return all(
            time.ticks_diff(current_time, self.last_pressed[button_id]) < self.TIME_WINDOW_MS
            for button_id in button_ids
        )

    def _advance_sequence(self):
        self.current_index += 1
        if self.current_index < len(self.current_sequence):
            self._activate_current_step()
        else:
            print("Sequence completed!")
            self.sequence_complete = True
