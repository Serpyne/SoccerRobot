#!/usr/bin/env python3

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3, INPUT_4
from datetime import datetime
from time import sleep
from os.path import join, dirname
import json

class CompassSensor(Sensor):
    def __init__(self, address, *args, **kwargs):
        super().__init__(driver_name="ht-nxt-compass", address=address, *args, **kwargs)
        self.angle = None
        self.mode = "COMPASS"
        self.command = "BEGIN-CAL"
        self.command = "END-CAL"

start_time = datetime.now()

times = {"times": []}

motors = [
    MediumMotor(OUTPUT_A),
    MediumMotor(OUTPUT_B),
    MediumMotor(OUTPUT_C),
    MediumMotor(OUTPUT_D)
]
motors[1].polarity = "inversed"
motors[3].polarity = "inversed"

compass = CompassSensor(INPUT_1)
original_orientation = compass.value()

while True:
    current = datetime.now() - start_time
    if current.seconds > 10:
        break

    for motor in motors:
        motor.run_forever(speed_sp=200)

    times["times"].append([current.total_seconds(), compass.value()])
    sleep(.01)

for motor in motors:
    motor.stop()

with open(join(dirname(__file__), "compass.json"), "w") as f:
    json.dump(times, f, sort_keys=True, indent=4)