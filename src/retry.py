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
        """RoboCup Robot Class"""

        self.gameplay_mode = ATTACK

        # Initialise Sensors and Motors
        self.ir_sensor = IRSeeker360(INPUT_1)
        self.compass_sensor = CompassSensor(driver_name="ht-nxt-compass", address=INPUT_2)
        self.us_sensors = {"x": UltrasonicSensor(INPUT_3),
                           "y": UltrasonicSensor(INPUT_4)}
        
        self.motors = [
            MediumMotor(OUTPUT_A), # LEFT    [0]
            MediumMotor(OUTPUT_B), # FRONT   [1]
            MediumMotor(OUTPUT_C), # RIGHT   [2]
            MediumMotor(OUTPUT_D)  # BACK    [3]
        ]

        # Calibrate compass sensor
        self.compass_sensor.command = "BEGIN-CAL"
        self.compass_sensor.command = "END-CAL"

        # Initialise screen menu
        self.display_menu = Menu((2, 2))
        self.display_menu.add_button(DisplayButton("Start Robot", "start", (0, 0)))
        self.display_menu.add_button(DisplayButton("Stop Robot", None, (self.display_menu.button_size[0], 0)))
        self.display_menu.add_button(DisplayButton("Kill Robot", "kill", (0, self.display_menu.button_size[1])))

        # Variables
        self.orientation = 0
        self.original_orientation = 0

        self.move_direction = None
        self.move_speed = None

        self.see_ball = False
        self.global_ball_angle = None

        self.pos = [0, 0]
        self.vel = [0, 0]

        self.tick = 0
        self.active = True

    def move(self, angle, speed=720):
        """Set move direction and speed of robot"""

        if angle != None:
            self.move_direction = angle % (2*pi)
            self.move_speed = speed

    def stop(self):
        """Set move direction and speed to None"""

        self.move_direction = None
        self.move_speed = None

    def wait(self, ms: int):
        """sleep(n ms) and tick(n)"""

        sleep(ms * .001)
        self.tick += ms

    def orientated_between(self, start, end) -> bool:
        """Returns True if robot is orientated between two values, False if it isn't."""

        start = (start % (2*pi))
        end = (end % (2*pi))
        if start < end:
            if self.orientation > start and self.orientation < end:
                return True
            else:
                return False
        elif start >= end:
            if (self.orientation > start) or (self.orientation < end):
                return True
            else:
                return False
            # raise Exception("orientated_between(self, start, end): start has to be less than end.")

    def run(self):
        """Run(): Start threads for robot"""

        threads = [
            threading.Thread(target=self.update_loop),
            threading.Thread(target=self.movement_loop),
            threading.Thread(target=self.menu_loop)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def update_loop(self):
        self.original_orientation = self.compass_sensor.value()

        while self.active:
            self.update()

        self.ir_sensor.close()
        return

    def update(self) -> bool:
        if (self.tick % 160) == 0: # Get sensor values every 160ms
            self.compass_sensor.angle = self.compass_sensor.value() - self.original_orientation
            self.orientation = radians(self.compass_sensor.angle) % (2*pi)

            self.relative_ball_angle, self.ball_strength = self.ir_sensor.read()
            self.relative_ball_angle_radians = (self.relative_ball_angle % 12) * pi/6
            self.global_ball_angle = (self.relative_ball_angle_radians + self.orientation) % (2*pi)
            
            self.see_ball = False
            if self.ball_strength > 0:
                self.see_ball = True

            dx = self.us_sensors["x"].value()
            dy = self.us_sensors["y"].value()

            if self.orientation == 0:
                dist_to_wall = dx
            elif self.orientated_between(0, pi/4):
                dist_to_wall = dx * cos(self.orientation)
            elif self.orientated_between(-pi/4, 0):
                dist_to_wall = dx * cos(abs(2*pi - self.orientation))
            else:
                dist_to_wall = None

            if dist_to_wall <= 850:
                self.move(pi/2)
            else:
                self.stop()

            self.pos[0] = dx
            self.pos[1] = dy

        # self.gameplay()
        
        # if (self.tick % 160) == 0: # display menu
        #     self.display_menu.draw()

        print(str(dist_to_wall))
        self.wait(10)

    def menu_loop(self):
        self.display_menu.update()

        if self.display_menu.command == "kill":
            self.active = False

    def gameplay(self):
        if self.gameplay_mode == ATTACK:
            self.move(pi)
        elif self.gameplay_mode == DEFENSE:
            self.move(0)

    def movement_loop(self):
        while self.active:
            self.movement()
        else: return

    def stop_all_motors(self):
        self.motors[0].stop()
        self.motors[1].stop()
        self.motors[2].stop()
        self.motors[3].stop()

    def movement(self):
        if self.move_direction == None or self.move_speed == None:
            self.stop_all_motors()
        else:
            self.vel[0] = cos(self.move_direction) * self.move_speed
            self.vel[1] = sin(self.move_direction) * self.move_speed

            if self.vel[0]:
                if self.vel[0] < 0:
                    self.motors[0].polarity = "normal"
                    self.motors[2].polarity = "inversed"
                    self.motors[0].run_forever(speed_sp=abs(self.vel[0]))
                    self.motors[2].run_forever(speed_sp=abs(self.vel[0]))
                elif self.vel[0] > 0:
                    self.motors[0].polarity = "inversed"
                    self.motors[2].polarity = "normal"
                    self.motors[0].run_forever(speed_sp=self.vel[0])
                    self.motors[2].run_forever(speed_sp=self.vel[0])
            if self.vel[1]:
                if self.vel[1] < 0:
                    self.motors[1].polarity = "normal"
                    self.motors[3].polarity = "inversed"
                    self.motors[1].run_forever(speed_sp=abs(self.vel[1]))
                    self.motors[3].run_forever(speed_sp=abs(self.vel[1]))
                elif self.vel[1] > 0:
                    self.motors[1].polarity = "inversed"
                    self.motors[3].polarity = "normal"
                    self.motors[1].run_forever(speed_sp=self.vel[1])
                    self.motors[3].run_forever(speed_sp=self.vel[1])

        if not self.active:
            self.stop_all_motors()
            return
        
        sleep(.05)

if __name__ == "__main__":
    robot = Robot()
    robot.run()