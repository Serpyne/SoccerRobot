#!/usr/bin/env python3

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from time import sleep
from math import sin, cos

motors = [
    MediumMotor(OUTPUT_A),
    MediumMotor(OUTPUT_B),
    MediumMotor(OUTPUT_C),
    MediumMotor(OUTPUT_D)
]

vel = [0, 0]
move_direction = 0

while True:
    vel[0] = cos(move_direction) * 800
    vel[1] = sin(move_direction) * 800
    move_direction += .1

    if vel[0]:
        if vel[0] < 0:
            motors[0].polarity = "normal"
            motors[2].polarity = "inversed"
            motors[0].run_forever(speed_sp=abs(vel[0]))
            motors[2].run_forever(speed_sp=abs(vel[0]))
        elif vel[0] > 0:
            motors[0].polarity = "inversed"
            motors[2].polarity = "normal"
            motors[0].run_forever(speed_sp=vel[0])
            motors[2].run_forever(speed_sp=vel[0])
    if vel[1]:
        if vel[1] < 0:
            motors[1].polarity = "normal"
            motors[3].polarity = "inversed"
            motors[1].run_forever(speed_sp=abs(vel[1]) * 1.66)
            motors[3].run_forever(speed_sp=abs(vel[1]) * 1.66)
        elif vel[1] > 0:
            motors[1].polarity = "inversed"
            motors[3].polarity = "normal"
            motors[1].run_forever(speed_sp=vel[1] * 1.66)
            motors[3].run_forever(speed_sp=vel[1] * 1.66)

    sleep(.01)