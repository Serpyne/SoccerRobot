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

from menu import *
from sensor import IRSeeker360

ATTACK = 0
DEFENSE = 1

FIELD_SIZE = [243, 182]

direction = 0
def move(r):
    global direction
    if r:
        direction = r % (2*pi)

def stop():
    global direction
    direction = None

tick = 0
def wait(t):
    global tick
    sleep(t)
    tick += t*100

def main_():
    global tick, direction

    current_strat = ATTACK

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

    data = json.load(open(join(dirname(__file__), "./options.json")))

    car_orientation = 0
    global_angle = 0
    angle = strength = None
    see_ball = False
    view_distance = None

    done_defense = False

    original_pos = [0, 0]
    pos = [0, 0]
    vel = [0, 0]

    display_menu = Menu((3, 3))

    while True:
        if display_menu.command == "start":
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

            # PSEUDOCODE

            if current_strat == ATTACK:                                                  # attacking mode
                done_defense = False
                if see_ball:                                                             # if the robot detects the ball (strength > 0)
                    if global_angle > 3*pi/2 and global_angle < pi/2:                    # if the ball is in front of the car
                        if global_angle > .2 and global_angle <= pi:                     # if ball is towards the right {.2r < a <= PIr}            
                            move(pi/2 - car_orientation)                                 # move right for 200 ms
                            wait(.2)
                        elif global_angle <= (2*pi - .2) and global_angle > pi:          # if ball is towards the left {PIr < a <= -.2r}
                            move(3*pi/2 - car_orientation)                               # move left for 200 ms
                            wait(.2)
                        else:                                                            # if its in front {-.2r <= a < .2r}
                            move(0)                                                      # move forward for 300 ms
                            wait(.3)
                        stop()
                        # waitforuserstop()
                    elif global_angle <= 3*pi/2 and global_angle >= pi/2:                # if the ball is behind the car
                        if abs(pi - global_angle) < .2:                                  # if it is directly behind the car
                            move(pi/2 - car_orientation)                                 # shmoove around 
                            wait(.2)                                                     # move right for 200 ms 
                        else:                                                            # if it isnt directly behind the car
                            move(pi - car_orientation)                                   # move back for 300 ms
                            wait(.3)
                        stop()
                else:
                    current_strat = DEFENSE

                if car_orientation:                                                      # if car orientation is detected
                    vel = [cos(direction)*720, sin(direction)*720]           # set vel to vector of direction angle

            elif current_strat == DEFENSE:                                               # defending mode
                # if (tick % 50) == 0:                                                     # every 500 ms
                #     a = atan2(original_pos[1]-pos[1], original_pos[0]-pos[0])            
                #     move(a)
                # if (tick % 200) == 0:
                #     a = pi * (randint(0, 1)+.5)
                #     move(a)

                dx = dy = None

                # IF ROBOT ROTATED 45 DEGREES LEFT AT ALL TIMES
                if (tick % 30) == 0: # every 300 ms
                    if view_distance:
                        if view_distance > 100: # if doesnt detect walls for 100cm (assuming ultrasonic is at the right position)
                            move(3*pi/2 - car_orientation) # move left in x direction

                        else:
                            dx = sqrt((view_distance**2) / 2) # same as c^2 = a^2 + b^2 (view_distance = sqrt(2*dx**2))
                            if dx < 85: # if x dist is less than 85cm
                                move(pi/2 - car_orientation) # move right for 200ms
                            wait(0.2)

                            view_distance = ultrasonic.distance_centimeters # take a second reading bc why not
                            dy = sqrt((view_distance**2) / 2)
                            if dy > 20: # if y dist is more than 20cm
                                move(pi - car_orientation) # move back to the goal

                # IF ROBOT IS FACING STRAIGHT FORWARD
                # if not done_defense:
                #     if view_distance:
                #         if (tick % 30) == 0:
                #             if compass_angle > 352 or compass_angle < 8: # if facing forward
                #                 dx = ultrasonic.distance_centimeters
                #                 for m in motors: # TURN LEFT 90 DEGREES
                #                     m.polarity = "normal" # TEST AT SCHOOL IF IT TURNS LEFT OR RIGHT (SHOULD BE LEFT)
                #                     m.run_forever(speed_sp=100)
                                
                #             else:
                #                 for m in motors:
                #                     m.polarity = "inverse"
                #                     m.run_forever(speed_sp=100)

                #             if compass_angle > 255 and compass_angle < 285:
                #                 dy = ultrasonic.distance_centimeters
                        
                #         if compass_angle > 255 and compass_angle < 285: # once it reaches left, stop
                #             for m in motors:
                #                 m.stop()
                #         if compass_angle > 352 or compass_angle < 8:
                #             for m in motors:
                #                 m.stop()
                #         done_defense = True
                    
                if see_ball:
                    current_strat = ATTACK

            if direction:
                vel[0] = cos(direction) * 720
                vel[1] = sin(direction) * 720
            else:
                vel[0] = 0
                vel[1] = 0

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

            translated_compass_angle = (compass_angle + 45) % 360                                                     # translate angle to correction
            if translated_compass_angle > 8 and translated_compass_angle < 352:                                       # if its in the correct angle already stop
                for m in motors:                                                                                      
                    m.stop()
            else:                                                                                                     # if its not the right orientation
                for m in motors:                                                                                      # set all four motors to rotate in the direction of the correction
                    if translated_compass_angle > 180:
                        m.polarity = "inversed"
                    elif translated_compass_angle <= 180:
                        m.polarity = "normal"
                    m.run_forever(speed_sp=[0, 180][translated_compass_angle>180] - (translated_compass_angle % 180)) # one rotation = 23.9cm travelled

            pos[0] += vel[0]
            pos[1] += vel[1]

        if (tick % 5) == 0 and display_menu.active: # display menu
            display_menu.update()
    
        if display_menu.command == "kill":          # display menu quit button
            break

        sleep(0.01)
        tick += 1

    sensor.close()

main_()
