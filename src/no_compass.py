#!/usr/bin/env python3

from time import sleep
from math import pi, cos, sin, radians

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
        self.command = "BEGIN-CAL"
        sleep(.5)
        self.command = "END-CAL"

class InfraredSensor(Sensor):
    def __init__(self, address, *args, **kwargs):
        super().__init__(driver_name="ht-nxt-ir-seek-v2", address=address, *args, **kwargs)
        self.mode = "DC-ALL"
        self.direction = None
    def get_direction(self):
        a = self.value(0)
        if a: self.direction = (a - 1) / 8 * pi
        else: self.direction = None

def average_two_angles_radians(a1, a2):
    d = ((a2 - a1 + pi/2) % pi) - pi/2
    return (a1 + d/2) % pi

active = True

def on_enter(state):
    global active
    if not state:
        active = not active

motors = [
            Motor(PORTS["MOTORS"][0]),                     # LEFT    [0]
            Motor(PORTS["MOTORS"][1], polarity_bias=-1, speed_bias=.6),   # FRONT   [1]
            Motor(PORTS["MOTORS"][2], polarity_bias=-1),   # RIGHT   [2]
            Motor(PORTS["MOTORS"][3], speed_bias=.6)                      # BACK    [3]
        ]

controls = Button()
controls.on_enter = on_enter

compass = CompassSensor(PORTS["COMPASS"])
ir = [
    InfraredSensor(PORTS["IR"][0]),
    InfraredSensor(PORTS["IR"][1])
]

relative_ball_direction = None

original_orientation = radians(compass.value()) % (2*pi)

def stop_motors():
    for motor in motors:
        motor.stop()

def move(angle_radians):
    # print(round((angle_radians % (2*pi)) * 180/pi, 3))
    vel = [cos(angle_radians) * MAX_SPEED, sin(angle_radians) * MAX_SPEED]

    motors[0].run(vel[0])
    motors[2].run(vel[0])
    motors[1].run(vel[1])
    motors[3].run(vel[1])

detection_extent = radians(35)

while True:
    if active:
        # move(-(radians(compass.value()) - original_orientation))
        # print(compass.value())
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
            move(relative_ball_direction - pi/2)
        else:
            print("ball not detected")
            stop_motors()
    else:
        stop_motors()

    controls.process()

    sleep(0.01)