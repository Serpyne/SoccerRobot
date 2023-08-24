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

        self.dx = self.dy = None
        self.dist_to_wall = None

        self.pos = [0, 0]
        self.vel = [0, 0]

        self.tick = 0
        self.active = True

        self.at_goal = False
        self.defense_going_back = False

        self.detection_extent = radians(25)

    def move(self, angle, speed=1080):
        """Set move direction and speed of robot"""

        if angle != None:
            self.move_direction = (angle - self.orientation) % (2*pi)
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

    def update_loop(self):
        self.original_orientation = self.compass_sensor.value()

        while self.active:
            try:
                self.update()
            except Exception as e: print("stopped for "+str(e))

        print("Stopping")
        self.ir_sensor.close()
        return

    def update(self):
        if (self.tick % 20) == 0: # Get sensor values every 20ms
            self.compass_sensor.angle = self.compass_sensor.value() - self.original_orientation
            self.orientation = radians(self.compass_sensor.angle) % (2*pi)

            self.relative_ball_angle, self.ball_strength = self.ir_sensor.read()
            self.relative_ball_angle_radians = (self.relative_ball_angle % 12) * pi/6
            self.global_ball_angle = (self.relative_ball_angle_radians + self.orientation) % (2*pi)
            
            self.see_ball = False
            if self.ball_strength > 1:
                self.see_ball = True

            # self.dx = self.us_sensors["x"].value()
            # self.dy = self.us_sensors["y"].value()

            # if self.orientation == 0:
            #     self.dist_to_wall = self.dx
            # elif self.orientated_between(0, pi/4):
            #     self.dist_to_wall = self.dx * cos(self.orientation)
            # elif self.orientated_between(-pi/4, 0):
            #     self.dist_to_wall = self.dx * cos(abs(2*pi - self.orientation))
            # else:
            #     self.dist_to_wall = None

            self.gameplay()

            if self.move_direction == None or self.move_speed == None:
                self.correct_rotation(0)

        self.wait(10)

    def correct_rotation(self, angle):
        a = (self.orientation - angle)
        if a < pi and a > self.detection_extent:
            polarity = "normal"
        elif a >= pi and a < 2*pi - self.detection_extent:
            polarity = "inversed"
        else:
            return
        for i, m in enumerate(self.motors):
            self.motors[i].polarity = polarity
            self.motors[i].run_forever(speed_sp=1080)

    def menu_loop(self):
        self.display_menu.update()
        self.display_menu.draw()

        if self.display_menu.command == "kill":
            self.active = False

    def gameplay(self):
        # print((str(round((self.global_ball_angle) * 180/pi)) + "    ")[:5] + (str(round((self.orientation) * 180/pi)) + "    ")[:5])
        if self.gameplay_mode == ATTACK:

            if self.global_ball_angle > 3*pi/2 or self.global_ball_angle < pi/2: # if in front half

                if self.ball_strength > 80:
                    self.move(0)
                else:
                    if self.global_ball_angle > 2*pi-self.detection_extent or self.global_ball_angle < self.detection_extent: # if directly in front
                        # self.move(self.relative_ball_angle_radians)
                        self.move(0) # move forward
                    else: # if not directly in front but in the front half
                        if self.global_ball_angle < pi:
                            self.move(pi/2, speed=720)
                        else:
                            self.move(3*pi/2, speed=720)

            else: # if in back half

                if self.global_ball_angle > pi - .3 and self.global_ball_angle < pi + .3: # if directly behind
                    self.move(3*pi/2) # hardcoded move out of the way
                else:
                    self.move(pi) # move straight back

        #     if not self.see_ball:
        #         self.gameplay_mode = DEFENSE

        # elif self.gameplay_mode == DEFENSE:
        #     if self.dist_to_wall:
        #         if self.dist_to_wall <= 850:
        #             self.move(pi/2)
        #         else:
        #             if self.at_goal:
        #                 self.stop()
        #             else:
        #                 self.move(pi)
        #                 self.overloaded_motors = ["overloaded" in x.state for x in self.motors]

        #     if self.see_ball:
        #         self.at_goal = False
        #         self.defense_going_back = False
        #         self.gameplay_mode = ATTACK
        # if self.see_ball:
        #     self.move(self.global_ball_angle)
        # else:
        #     self.stop()

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
        
        sleep(.005)

if __name__ == "__main__":
    robot = Robot()
    robot.run()