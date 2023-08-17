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

direction = 0
def move(r):
    global direction
    if r:
        direction = r % (2*pi)

def stop():
    global direction
    direction = None

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

    movement_dir = "x"

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

        # IF ROBOT ROTATED 45 DEGREES LEFT AT ALL TIMES
        view_distance = ultrasonic.distance_centimeters

        if view_distance:
            dx = sqrt((view_distance**2) / 2) # same as c^2 = a^2 + b^2 (view_distance = sqrt(2*dx**2))
            if view_distance > 100: # if doesnt detect walls for 100cm (assuming ultrasonic is at the right position)
                move(3*pi/2 - car_orientation) # move left in x direction
            else:
                move(pi/2 - car_orientation) # move right
                movement_dir = "x"
            
            if dx > 90:                         # if dist x or y from wall is more than 90cm
                if movement_dir == "x":         # if currently moving in x dir
                    stop()                      # stop
                    movement_dir = "y"          # now exclusively moving in y dir
                elif movement_dir == "y":       
                    move(pi - car_orientation)  # move back to goal
            elif dx < 8:
                if movement_dir == "y":
                    stop()                      # stop once dist is less than 8 cm

        vel[0] = cos(direction) * 720
        vel[1] = sin(direction) * 720

        if vel[0] == 0:
            motors[0].stop()
            motors[2].stop()
        elif vel[0] < 0:
            motors[0].polarity = "normal"
            motors[2].polarity = "inversed"
            motors[0].run_forever(speed_sp=abs(vel[0]))
            motors[2].run_forever(speed_sp=abs(vel[0]))
        elif vel[0] > 0:
            motors[0].polarity = "inversed"
            motors[2].polarity = "normal"
            motors[0].run_forever(speed_sp=vel[0])
            motors[2].run_forever(speed_sp=vel[0])

        if vel[1] == 0:
            motors[1].stop()
            motors[3].stop()
        elif vel[1] < 0:
            motors[1].polarity = "normal"
            motors[3].polarity = "inversed"
            motors[1].run_forever(speed_sp=abs(vel[1]))
            motors[3].run_forever(speed_sp=abs(vel[1]))
        elif vel[1] > 0:
            motors[1].polarity = "inversed"
            motors[3].polarity = "normal"
            motors[1].run_forever(speed_sp=vel[1])
            motors[3].run_forever(speed_sp=vel[1])
               

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
        
        sleep(0.01)
        tick += 1

    sensor.close()

main_()
