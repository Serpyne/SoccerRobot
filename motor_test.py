#!/usr/bin/env python3

from time import sleep as sl
from math import pi, sin, cos
from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D

motors = [
    MediumMotor(OUTPUT_A),
    MediumMotor(OUTPUT_B),
    MediumMotor(OUTPUT_C),
    MediumMotor(OUTPUT_D)
]

a = 0
while True:
    vel = [cos(a)*720, sin(a)*720]

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

    a = (a + .1) % (pi*2)

    sl(0.05)