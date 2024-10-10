# tankdrive.py - By: Aengus, Izzy, Tyler - Tue Oct 8 2024
from machine import PWM

class Motors:
    '''
    example usage:
                    lf,      lb,      rf,      rb
    motors = Motors(Pin(27), Pin(26), Pin(19), Pin(21))
    motors.drive(1.0, -1.0)
    '''
    def __init__(self, lf, lb, rf, rb):
        self.pwm_LF = PWM(lf)
        self.pwm_LF.freq(20000)
        self.pwm_LF.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_LB = PWM(lb)
        self.pwm_LB.freq(20000)
        self.pwm_LB.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_RF = PWM(rf)
        self.pwm_RF.freq(20000)
        self.pwm_RF.duty_u16(0) # can be any positive integer 0-1023

        self.pwm_RB = PWM(rb)
        self.pwm_RB.freq(20000)
        self.pwm_RB.duty_u16(0) # can be any positive integer 0-1023

    def drive(self, left, right): # where each is a float between -1.0 and 1.0
        '''
        test cases to catch:
        both arguments must be numbers
        if the numbers are out of range, round them into range
        '''
        #print('about to drive motors with {}, {}'.format(left, right))
        assert isinstance(left, float) or isinstance(left, int)
        assert isinstance(right, float) or isinstance(right, int)
        if left < -1:
            left = -1
        if left > 1:
            left = 1
        if right < -1:
            right = -1
        if right > 1:
            right = 1
        if left == 0: # stop both left ones
            self.pwm_LF.duty_u16(0)
            self.pwm_LB.duty_u16(0)
        elif left > 0: # left forward
            self.pwm_LF.duty_u16(int(65535/2 * left))
            self.pwm_LB.duty_u16(0)
        elif left < 0: # left backward
            self.pwm_LF.duty_u16(0)
            self.pwm_LB.duty_u16(int(-65535/2 * left))
        if right == 0: # stop both right ones
            self.pwm_RF.duty_u16(0)
            self.pwm_RB.duty_u16(0)
        elif right > 0: # right forward
            self.pwm_RF.duty_u16(int(65535/2 * right))
            self.pwm_RB.duty_u16(0)
        elif right < 0: # right backward
            self.pwm_RF.duty_u16(0)
            self.pwm_RB.duty_u16(int(-65535/2 * right))

    def interpret_throttle_angle(self, throttle, angle):
        angle = angle % 360
        if angle == 0:
            return throttle, throttle
        if 0< angle < 180:
            #return throttle, throttle*(1-angle/45)
            return throttle*(1-angle/45), throttle
        if 180 < angle:
            #return throttle*((angle-315)/45), throttle
            return throttle, throttle*((angle-315)/45)
        raise AssertionError
        raise AssertionError
