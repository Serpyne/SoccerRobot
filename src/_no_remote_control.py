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

from menu import *
from sensor import IRSeeker360

ATTACK = 0
DEFENSE = 1

direction = 0
def move(r):
    global direction
    if r:
        direction = r

def stop():
    global direction
    direction = None

def main_():
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
    original_angle = compass.value()

    data = json.load(open(join(dirname(__file__), "./options.json")))

    car_orientation = 0
    global_angle = 0
    angle = strength = None
    see_ball = False

    original_pos = [0, 0]
    pos = [0, 0]
    vel = [0, 0]

    tick = 0

    display_menu = Menu((3, 3))

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

        # PSEUDOCODE

        if current_strat == ATTACK:                                                  # attacking mode
            if see_ball:
                if global_angle > 3*pi/2 and global_angle < pi/2:
                    move(pi/2 - car_orientation)
                    # waitforuserstop()
                elif global_angle <= 3*pi/2 and global_angle >= pi/2:
                    if abs(pi - global_angle) < .2:
                        move(pi/2 - car_orientation)
                        sleep(.4) # move right for .4 seconds
                    move(pi - car_orientation)
            else:
                current_strat = DEFENSE

            if car_orientation:
                vel = [cos(car_orientation)*720, sin(car_orientation)*720]

        elif current_strat == DEFENSE:                                              # defending mode
            if (tick % 50) == 0:
                a = atan2(original_pos[1]-pos[1], original_pos[0]-pos[0])
                move(a)
            if (tick % 200) == 0:
                a = pi * (randint(0, 1)+.5)
                move(a)

            if see_ball:
                current_strat = ATTACK

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

        if compass_angle > 8 and compass_angle < 352:                                # correcting rotation
            for m in motors:
                if compass_angle > 180:
                    m.polarity = "inversed"
                elif compass_angle <= 180:
                    m.polarity = "normal"
                m.run_forever(speed_sp=[0, 180][compass_angle>180] - (compass_angle % 180)) # one rotation = 23.9cm travelled
        else:
            for m in motors:
                m.stop()

        pos[0] += vel[0]
        pos[1] += vel[1]

        sleep(0.01)
        tick += 1

        if (tick % 5) == 0 and display_menu.active:
            display_menu.update()
    
        if display_menu.command == "kill":
            break

    sensor.close()

main_()
