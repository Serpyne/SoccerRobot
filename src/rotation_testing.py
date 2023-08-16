#!/usr/bin/env python3

"""
THE PROGRAM WHICH CONTROLS THE ROBOT; MUST BE RUN ON THE ROBOT OTHERWISE IT WONT WORK.
"""

from time import sleep
import sys, threading, json
from os.path import join, dirname
from random import randint
from math import pi, cos, sin, radians, atan2, sqrt

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.led import Leds

from sensor import IRSeeker360

def main_():
    sensor = IRSeeker360(INPUT_1)
    ultrasonic = UltrasonicSensor(INPUT_3)

    motors = [
        MediumMotor(OUTPUT_A),      # BACK        [0]
        MediumMotor(OUTPUT_B),      # LEFT       [1]
        MediumMotor(OUTPUT_C),      # FRONT       [2]
        MediumMotor(OUTPUT_D)       # RIGHT        [3]
    ]

    compass = Sensor(driver_name="ht-nxt-compass", address=INPUT_2)
    compass.mode = "COMPASS"
    compass_angle = 0
    original_angle = compass.value()

    car_orientation = 0
    global_angle = 0
    angle = strength = None
    see_ball = False
    view_distance = None

    original_pos = [0, 0]
    pos = [0, 0]
    vel = [0, 0]

    tick = 0

    while True:
        # Button logic
        compass_angle = compass.value() - original_angle                             # read compass sensor
        car_orientation = radians(compass_angle)

        angle, strength = sensor.read()                                              # read ir seeker angle + strength
        a = (angle % 12) * pi/6
        global_angle = a + car_orientation                                           # angle of ball in global scene
        see_ball = False
        if strength > 0:
            see_ball = True

        if (tick % 30) == 0: # every 300ms
            view_distance = ultrasonic.distance_centimeters

        translated_compass_angle = (compass_angle + 45) % 360
        if translated_compass_angle > 8 and translated_compass_angle < 352:                                # correcting rotation
            for m in motors:
                if translated_compass_angle > 180:
                    m.polarity = "inversed"
                elif translated_compass_angle <= 180:
                    m.polarity = "normal"
                m.run_forever(speed_sp=[0, 180][translated_compass_angle>180] - (translated_compass_angle % 180)) # one rotation = 23.9cm travelled
        else:
            for m in motors:
                m.stop()
        
        # Test this                                                                                                
        # if view_distance:
        #     if (tick % 30) == 0:
        #         if compass_angle > 352 or compass_angle < 8: # if facing forward
        #             dx = ultrasonic.distance_centimeters
        #             for m in motors: # TURN LEFT 90 DEGREES
        #                 m.polarity = "normal" # TEST AT SCHOOL IF IT TURNS LEFT OR RIGHT (SHOULD BE LEFT)
        #                 m.run_forever(speed_sp=100)
                    
        #         else:
        #             for m in motors:
        #                 m.polarity = "inverse"
        #                 m.run_forever(speed_sp=100)

        #         if compass_angle > 255 and compass_angle < 285:
        #             dy = ultrasonic.distance_centimeters
            
        #     if compass_angle > 255 and compass_angle < 285: # once it reaches left, stop
        #         for m in motors:
        #             m.stop()
        #     if compass_angle > 352 or compass_angle < 8:
        #         for m in motors:
        #             m.stop()

        sleep(0.01)
        tick += 1

    sensor.close()

main_()
