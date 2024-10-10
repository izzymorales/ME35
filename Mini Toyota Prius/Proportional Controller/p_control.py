# p_control.py - By: Aengus, Izzy, Tyler - Tue Oct 8 2024
# To run automatically when cam gets power, rename main.py

from machine import Pin, PWM
import sensor
import time
import math

from tankdrive import Motors

motors = Motors(Pin('P4', Pin.OUT), Pin('P5', Pin.OUT), Pin('P8', Pin.OUT), Pin('P7', Pin.OUT))

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA) # changing to QVGA (320x240) from QQVGA, makes it slower
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must turn this off to prevent image washout...
sensor.set_auto_whitebal(False)  # must turn this off to prevent image washout...
clock = time.clock()

# f_x is the x focal length of the camera. It should be equal to the lens focal length in mm
# divided by the x sensor size in mm times the number of pixels in the image.
# The below values are for the OV7725 camera with a 2.8 mm lens.

# f_y is the y focal length of the camera. It should be equal to the lens focal length in mm
# divided by the y sensor size in mm times the number of pixels in the image.
# The below values are for the OV7725 camera with a 2.8 mm lens.

# c_x is the image x center position in pixels.
# c_y is the image y center position in pixels.

f_x = (2.8 / 3.984) * 160  # find_apriltags defaults to this if not set
f_y = (2.8 / 2.952) * 120  # find_apriltags defaults to this if not set
c_x = 160 * 0.5  # find_apriltags defaults to this if not set (the image.w * 0.5)
c_y = 120 * 0.5  # find_apriltags defaults to this if not set (the image.h * 0.5)


def degrees(radians):
    return (180 * radians) / math.pi

last_tag_seen = 0
no_tag_timeout = 1  # time in seconds before car stops after not detecting apriltag

while True:
    clock.tick()
    img = sensor.snapshot()
    tags_we_see = img.find_apriltags(fx=f_x, fy=f_y, cx=c_x, cy=c_y)
    if tags_we_see:
        for tag in tags_we_see:  # defaults to TAG36H11
            img.draw_rectangle(tag.rect, color=(255, 0, 0))
            img.draw_cross(tag.cx, tag.cy, color=(0, 255, 0))
            print_args = (
                tag.x_translation,
                tag.y_translation,
                tag.z_translation,
                degrees(tag.x_rotation),
                degrees(tag.y_rotation),
                degrees(tag.z_rotation),
            )
            # Translation units are unknown. Rotation units are in degrees.
            #print(tag.x_translation)
            #print("Tx: %f, Ty %f, Tz %f, Rx %f, Ry %f, Rz %f" % print_args)
            current_angle = tag.x_translation # range -7 to 7
            current_dist = -1 * tag.z_translation
            target_angle = 0 # car should turn right when angle is negative, left when angle is positive
            target_dist = 7
            kp_vel = 0.1
            kp_steer = 10
            throttle = kp_vel * (current_dist - target_dist)
            angle = kp_steer * (current_angle - target_angle)
            print("about to drive with {}, {}".format(throttle, angle))
            motors.drive(*motors.interpret_throttle_angle(throttle, angle))
            last_tag_seen = time.time()
    else: # april tag not being detected, check how long its been since last detection
        time_since_tag = time.time() - last_tag_seen
        if time_since_tag < no_tag_timeout:
            print('no apriltag, driving slowly forward')
            motors.drive(*motors.interpret_throttle_angle(0.4, 0))  # moves
        else:
            print('no apriltag for too long, stopping')
            motors.drive(*motors.interpret_throttle_angle(0, 0))  # car stops

        motors.drive(*motors.interpret_throttle_angle(throttle, angle))
    if not tags_we_see:
        print('no april tag was seen')
        motors.drive(*motors.interpret_throttle_angle(0, 0)) # stop driving
