#!/usr/bin/env python3

"""
THE PROGRAM WHICH CONTROLS THE ROBOT; MUST BE RUN ON THE ROBOT OTHERWISE IT WONT WORK.
"""

from time import sleep
import sys, threading, json
from os.path import join, dirname
from random import randint
from math import pi, cos, sin, radians, atan2

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3
from ev3dev2.led import Leds

from sensor import IRSeeker360

# Initalise sensors
leds = Leds()

ATTACK = 0
DEFENSE = 1
current_strat = ATTACK

sensor = IRSeeker360(INPUT_1)

motors = [
    MediumMotor(OUTPUT_A),      # LEFT        [0]
    MediumMotor(OUTPUT_B),      # FRONT       [1]
    MediumMotor(OUTPUT_C),      # RIGHT       [2]
    MediumMotor(OUTPUT_D)       # BACK        [3]
]
compass = Sensor(driver_name="ht-nxt-compass", address=INPUT_2)
compass.mode = "COMPASS"
compass_angle = 0

data = json.load(open(join(dirname(__file__), "./options.json")))

car_orientation = 0
direction = 0

see_ball = False
mode = "attacking"

spin_angle = 0 

original_pos = [0, 0]

pos = [0, 0]
vel = [0, 0]
angle = strength = None

def move(r):
    global car_orientation
    if r:
        car_orientation = r

def stop():
    global car_orientation
    car_orientation = None

def main_():
    """Main loop which controls the button press, and getting the compass and colour sensor values."""
    global angle, strength, vel, pos, compass_angle, see_ball, car_orientation, spin_angle, current_strat
    while True:
        # Button logic
        compass_angle = compass.value()
        car_orientation = radians(compass_angle)

        # PSEUDOCODE

        if current_strat == ATTACK:
            if see_ball:
                if car_orientation > 3*pi/2 and car_orientation < pi/2:
                    move(pi/2 - car_orientation)
                    # waitforuserstop()
                elif car_orientation <= 3*pi/2 and car_orientation >= pi/2:
                    # hard_coded_move_behind_the_ball()
                    pass
            else:
                a = atan2(original_pos[1]-pos[1], original_pos[0]-pos[0])
                move(a)
                current_strat = DEFENSE

            angle, strength = sensor.read()
            a = (angle % 12) * pi/6 #+ (compass_angle * pi/180) #+ pi/4

            if car_orientation:
                vel = [cos(car_orientation)*720, sin(car_orientation)*720]

        elif current_strat == DEFENSE:
            move(spin_angle)
            spin_angle += .2

            if see_ball:
                current_strat = ATTACK

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
        pos[0] += vel[0]
        pos[1] += vel[1]

        sleep(0.01)

main_()

sensor.close()