#!/usr/bin/env python3

"""
THE PROGRAM WHICH CONTROLS THE ROBOT; MUST BE RUN ON THE ROBOT OTHERWISE IT WONT WORK.
"""

from time import sleep
import socket, sys, threading, json
from os.path import join, dirname
from random import randint
from math import pi, cos, sin, atan2, radians, sqrt

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.led import Leds

from sensor import IRSeeker360

# Initalise sensors
leds = Leds()

ATTACK = 0
DEFENSE = 1
current_strat = ATTACK

ir_sensor = IRSeeker360(INPUT_1)

motors = None
gyroscope = gyro_angle = None
colour_sensor = sensed_colour = None
ts = None
can_press = False

motors = [
    MediumMotor(OUTPUT_A), # FRONT  [0]
    MediumMotor(OUTPUT_B), # RIGHT  [1]
    MediumMotor(OUTPUT_C), # BACK   [2]
    MediumMotor(OUTPUT_D)  # LEFT   [3]
]
compass = Sensor(driver_name="ht-nxt-compass", address=INPUT_2)
compass.command = "BEGIN-CAL"
compass.command = "END-CAL"
# compass.mode = "COMPASS"
compass_angle = 0
ultrasonic = UltrasonicSensor(INPUT_3)

pos = [0, 0]
vel = [0, 0]
angle = strength = None

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
    """Main loop which controls the button press, and getting the compass and colour sensor values."""
    global gyro_angle, sensed_colour, angle, strength, vel, pos, compass_angle, angle, strength, can_press, motors, current_strat
    original_angle = compass.value()
    while True:
        compass_angle = compass.value() - original_angle                             # read compass sensor
        car_orientation = radians(compass_angle)

        angle, strength = ir_sensor.read()                                             # read ir seeker angle + strength
        a = (angle % 12) * pi/6
        global_angle = (a + car_orientation) % (2*pi)                                           # angle of ball in global scene
        see_ball = False
        if strength > 0:
            see_ball = True
            # print(str((global_angle%(2*pi))*180/pi), "degrees")

        if (tick % 30) == 0: # every 300ms
            view_distance = ultrasonic.distance_centimeters

        current_strat = ATTACK
        if current_strat == ATTACK:                                                  # attacking mode
            if see_ball:                                                             # if the robot detects the ball (strength > 0)
                print("pass 1")
                if global_angle > 3*pi/2 and global_angle < pi/2:                    # if the ball is in front of the car
                    print("pass 1")
                    if global_angle > .2 and global_angle <= pi:                     # if ball is towards the right {.2r < a <= PIr}
                        print("right()")            
                        move(pi/2 - car_orientation)                                 # move right for 200 ms
                        wait(.2)
                    elif global_angle <= (2*pi - .2) and global_angle > pi:          # if ball is towards the left {PIr < a <= -.2r}
                        print("left()")            
                        move(-pi/2 - car_orientation)                               # move left for 200 ms
                        wait(.2)
                    elif global_angle > 2*pi-.2 or global_angle < .2:                # if its in front {-.2r <= a < .2r}
                        move(0)                                                      # move forward for 300 ms
                        print("forward()")
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

        elif current_strat == DEFENSE:
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

            if see_ball:
                current_strat = ATTACK

def movement_thread():
    global vel, motors, pos
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

    wait(0.01)

threads = [
    threading.Thread(target=main_),
    threading.Thread(target=movement_thread)
]

for t in threads:
    t.start()

for t in threads:
    t.join()