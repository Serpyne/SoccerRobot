#!/usr/bin/env python3

from time import sleep
import threading
from os.path import join, dirname
from math import pi, cos, sin, atan2, radians, sqrt

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.led import Leds

from sensor import IRSeeker360
from menu import DisplayButton, Menu

ATTACK = 0
DEFENSE = 1

FIELD_SIZE = [243, 182]

class CompassSensor(Sensor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = None

class Robot:
    def __init__(self):
        self.gameplay_mode = ATTACK

        self.ir_sensor = IRSeeker360(INPUT_1)
        self.compass_sensor = CompassSensor(driver_name="ht-nxt-compass", address=INPUT_2)
        self.us_sensors = {"x": UltrasonicSensor(INPUT_3),
                           "y": UltrasonicSensor(INPUT_4)}
        self.motors = [
            MediumMotor(OUTPUT_A), # FRONT  [0]
            MediumMotor(OUTPUT_B), # RIGHT  [1]
            MediumMotor(OUTPUT_C), # BACK   [2]
            MediumMotor(OUTPUT_D)  # LEFT   [3]
        ]

        self.compass_sensor.command = "BEGIN-CAL"
        self.compass_sensor.command = "END-CAL"

        self.orientation = 0
        self.original_orientation = 0
        self.move_direction = None
        self.move_speed = None
        self.tick = 0

        self.see_ball = False
        self.global_ball_angle = None

        self.pos = [0, 0]
        self.vel = [0, 0]

        self.display_menu = Menu((2, 2))
        self.display_menu.add_button(DisplayButton("Start Robot", "start", (0, 0)))
        self.display_menu.add_button(DisplayButton("Stop Robot", None, (display_menu.button_size[0], 0)))
        self.display_menu.add_button(DisplayButton("Kill Robot", "kill", (0, display_menu.button_size[1])))

    def move(self, angle, speed=100):
        if angle:
            self.move_direction = angle % (2*pi)
            self.move_speed = speed

    def stop(self):
        self.move_direction = None
        self.move_speed = None

    def wait(self, ms):
        """sleep(n ms) and tick(n)"""
        sleep(ms * .001)
        self.tick += ms


    def run(self):
        threads = [
            threading.Thread(target=self.update_loop),
            threading.Thread(target=self.movement)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def update_loop(self):
        self.original_orientation = self.compass_sensor.value()

        while True:
            self.update()

    def update(self):
        if (self.tick % 160) == 0: # Get sensor values every 160ms
            self.compass_sensor.angle = self.compass_sensor.value() - self.original_orientation                             # read compass sensor
            self.orientation = radians(self.compass_sensor.angle)

            self.relative_ball_angle, self.ball_strength = self.ir_sensor.read()                                             # read ir seeker angle + strength
            self.relative_ball_angle_radians = (self.relative_ball_angle % 12) * pi/6
            self.global_ball_angle = (self.relative_ball_angle_radians + self.orientation) % (2*pi)                                           # angle of ball in global scene
            self.see_ball = False
            if self.ball_strength > 0:
                self.see_ball = True

            view_distance = self.us_sensors["x"].distance_centimeters

        self.gameplay()
        self.movement()

    def gameplay(self):
        if self.gameplay_mode == ATTACK:
            pass

    def movement(self):
        if self.vel[0] == 0:
            self.motors[0].stop()
            self.motors[2].stop()
        elif self.vel[0] < 0:
            self.motors[0].polarity = "normal"
            self.motors[2].polarity = "inversed"
            self.motors[0].run_forever(speed_sp=abs(self.vel[0]))
            self.motors[2].run_forever(speed_sp=abs(self.vel[0]))
        elif self.vel[0] > 0:
            self.motors[0].polarity = "inversed"
            self.motors[2].polarity = "normal"
            self.motors[0].run_forever(speed_sp=self.vel[0])
            self.motors[2].run_forever(speed_sp=self.vel[0])
        if self.vel[1] == 0:
            self.motors[1].stop()
            self.motors[3].stop()
        elif self.vel[1] < 0:
            self.motors[1].polarity = "normal"
            self.motors[3].polarity = "inversed"
            self.motors[1].run_forever(speed_sp=abs(self.vel[1]))
            self.motors[3].run_forever(speed_sp=abs(self.vel[1]))
        elif self.vel[1] > 0:
            self.motors[1].polarity = "inversed"
            self.motors[3].polarity = "normal"
            self.motors[1].run_forever(speed_sp=self.vel[1])
            self.motors[3].run_forever(speed_sp=self.vel[1])

        sleep(.01)