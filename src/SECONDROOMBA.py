#!/usr/bin/env python3

import json
from os.path import join, dirname
from time import sleep
from math import pi, cos, sin, radians
from random import uniform

from ev3dev2.button import Button
from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3, INPUT_4

PORTS = {
    "MOTORS":   [OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D],
    "COMPASS":   INPUT_1,
    "IR":        [INPUT_3, INPUT_4]
}

MAX_SPEED = 1560

class Motor(MediumMotor):
    def __init__(self, address, polarity_bias:int=1, speed_bias=1, *args, **kwargs):
        super().__init__(address=address, *args, **kwargs)
        self.polarity_bias = (abs(int(polarity_bias)) // int(polarity_bias)) if polarity_bias != 0 else 1
        self.speed_bias = max(0.01, min(1, abs(speed_bias)))

    def run(self, speed):
        if speed * self.polarity_bias > 0:
            self.polarity = "normal"
        elif speed * self.polarity_bias < 0:
            self.polarity = "inversed"
        self.run_forever(speed_sp=abs(speed) * self.speed_bias)

class CompassSensor(Sensor):
    def __init__(self, address, *args, **kwargs):
        super().__init__(driver_name="ht-nxt-compass", address=address, *args, **kwargs)
        self.angle = None
        self.mode = "COMPASS"
        self.command = "BEGIN-CAL"
        self.command = "END-CAL"

class InfraredSensor(Sensor):
    def __init__(self, address, *args, **kwargs):
        super().__init__(driver_name="ht-nxt-ir-seek-v2", address=address, *args, **kwargs)
        self.mode = "AC-ALL"
        self.direction = None
        self.strength = 0
    def get_direction(self):
        a = self.value(0)
        if a: self.direction = (a - 1) / 8 * pi
        else: self.direction = None
        s = self.value(1)
        if a: self.strength = int(s)
        else: self.strength = 0

def average_two_angles_radians(a1, a2):
    d = ((a2 - a1 + pi/2) % (pi)) - pi/2
    return (a1 + d/2) % (pi)

active = False
print("Started")

def on_enter(state):
    global active, original_orientation
    if not state:
        active = not active
        print("Paused Running".split()[int(active)])
    else:
        original_orientation = correct_compass(compass.value())

data = json.load(open(join(dirname(__file__), "compass.json"), "r"))
min_angle = min([x[1] for x in data["times"]])
max_angle = max([x[1] for x in data["times"]])
def correct_compass(angle):
    a = max(min_angle, max(min_angle, angle))
    t = (a - min_angle) / (max_angle - min_angle)
    return t * 2 * pi



motors = [
            Motor(PORTS["MOTORS"][0]),                     # LEFT    [0]
            Motor(PORTS["MOTORS"][1], polarity_bias=-1, speed_bias=1),   # FRONT   [1]
            Motor(PORTS["MOTORS"][2], polarity_bias=-1),   # RIGHT   [2]
            Motor(PORTS["MOTORS"][3], speed_bias=1)                      # BACK    [3]
        ]

controls = Button()
controls.on_enter = on_enter

compass = CompassSensor(PORTS["COMPASS"])
compass.mode = "COMPASS"
compass.command = "BEGIN-CAL"
compass.command = "END-CAL"
ir = [
    InfraredSensor(PORTS["IR"][0]),
    InfraredSensor(PORTS["IR"][1])
]

relative_ball_direction = None

original_orientation = correct_compass(compass.value())

def stop_motors():
    for motor in motors:
        motor.stop()

def move(angle_radians):
    vel = [int(cos(angle_radians - pi) * MAX_SPEED), int(sin(angle_radians - pi) * MAX_SPEED)]

    if vel[0]:
        motors[0].run(vel[0])
        motors[2].run(vel[0])
    else:
        motors[0].stop()
        motors[2].stop()
    if vel[1]:
        motors[1].run(vel[1])
        motors[3].run(vel[1])
    else:
        motors[1].stop()
        motors[3].stop()

    return vel

detection_extent = radians(30)
forward = radians(30)
facing_forward = True
turned = False

first_time_not_seeing_ball = False
see_ball = False

move_dir = 0

while True:
    if active:
        orientation = (correct_compass(compass.value()) - original_orientation) % (2*pi)
        if facing_forward:
            for sensor in ir:
                sensor.get_direction()
            
            relative_ball_direction = None
            if ir[0].direction and not ir[1].direction:
                a1 = ir[0].direction
                relative_ball_direction = a1
            elif not ir[0].direction and ir[1].direction:
                a2 = ir[1].direction + pi
                relative_ball_direction = a2
            elif ir[0].direction and ir[1].direction:
                a1 = ir[0].direction
                a2 = ir[1].direction + pi
                relative_ball_direction = average_two_angles_radians(a1, a2)
                
            if relative_ball_direction:
                relative_ball_direction = (relative_ball_direction - pi/2) % (2*pi)
                if relative_ball_direction > 3*pi/2 or relative_ball_direction < pi/2:
                    if relative_ball_direction > 2*pi-detection_extent or relative_ball_direction < detection_extent:
                        move(0)
                    else:
                        if relative_ball_direction < pi:
                            move(pi/2)
                        else:
                            move(3*pi/2)
                else:
                    if max(ir[0].strength, ir[1].strength) > 2:
                        backward = radians(10)
                    else:
                        backward = radians(5)
                    if relative_ball_direction > pi - backward and relative_ball_direction < pi + backward:
                        move(2*pi/3)
                    else:
                        move(pi)
                
                first_time_not_seeing_ball = False
                see_ball = True
            else:
                if first_time_not_seeing_ball:
                    move_dir = 0
                    first_time_not_seeing_ball = True
                
                stalled = False
                for motor in motors:
                    if motor.STATE_STALLED in motor.state:
                        stalled = True
                        break

                if stalled:
                    move_dir = (move_dir + uniform(-.1, .5)) % (2*pi)

                move(move_dir)

                see_ball = False

        if see_ball:
            if orientation > (2*pi) - forward or orientation < forward:
                if not turned:
                    stop_motors()
                    facing_forward = True
                    turned = True
            else:
                turn = 400
                vel = [int(cos(relative_ball_direction - pi) * (MAX_SPEED - turn)), int(sin(relative_ball_direction - pi) * (MAX_SPEED - turn))]
                if orientation < pi/2:
                    motors[0].run(turn)
                    motors[1].run(turn)
                    motors[2].run(-turn)
                    motors[3].run(-turn)
                elif orientation >= 3*pi/2:
                    motors[0].run(-turn)
                    motors[1].run(-turn)
                    motors[2].run(turn)
                    motors[3].run(turn)
                else:
                    motors[0].run(-turn)
                    motors[1].run(-turn)
                    motors[2].run(turn)
                    motors[3].run(turn)
                facing_forward = False
                turned = False
    else:
        stop_motors()

    controls.process()

    sleep(0.01)