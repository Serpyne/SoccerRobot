#!/usr/bin/env python3

import threading, json, socket
from time import sleep
from os.path import join, dirname
from math import pi, cos, sin, radians

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3, INPUT_4

from sensor import IRSeeker360

DEBUG = None

MAX_SPEED = 1560

class Motor(MediumMotor):
    def __init__(self, polarity_bias=1, speed_bias=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.polarity_bias = abs(polarity_bias)/polarity_bias if polarity_bias != 0 else 1
        self.speed_bias = max(0.01, min(1, abs(speed_bias)))
    def run(self, speed):
        if speed * self.polarity_bias > 0:
            self.polarity = "normal"
        elif speed * self.polarity_bias < 0:
            self.polarity = "inversed"
        self.run_forever(speed_sp=abs(speed) * self.speed_bias)

class CompassSensor(Sensor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = None
        self.command = "BEGIN-CAL"
        self.command = "END-CAL"

class Robot:
    def __init__(self):
        """RoboCup Robot Class"""

        self.ir_sensor = IRSeeker360(INPUT_4)
        self.compass_sensor = CompassSensor(driver_name="ht-nxt-compass", address=INPUT_3)

        self.motors = [
            MediumMotor(OUTPUT_A), # LEFT    [0]
            MediumMotor(OUTPUT_B), # FRONT   [1]
            MediumMotor(OUTPUT_C), # RIGHT   [2]
            MediumMotor(OUTPUT_D)  # BACK    [3]
        ]

        self.orientation = 0
        self.original_orientation = 0

        self.move_direction = None
        self.move_speed = None

        self.see_ball = False
        self.global_ball_angle = None

        self.active = False

        self.at_goal = False
        self.defense_going_back = False

        self.detection_extent = radians(31)

        self.tick = 0

        # client initialisation
        data = json.load(open(join(dirname(__file__), "./options.json")))
        target_host = data["host_address"]
        target_port = data["host_port"]

        self.client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.client.settimeout(1)
        self.client.connect((target_host, target_port))
        print("Connected")

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

    def run(self):
        """Run(): Start threads for robot"""

        threads = [
            threading.Thread(target=self.update_loop),
            threading.Thread(target=self.movement_loop),
            threading.Thread(target=self.request_handler)
        ]

        for t in threads:
            t.start()

    def request_handler(self):
        while True:
            request = self.client.recv(1024)
            if request:
                self.process_request(request.decode())

    def process_request(self, content):
        match 

    def update_loop(self):
        self.original_orientation = self.compass_sensor.value()

        while True:
            if self.active:
                try:
                    self.update()
                except Exception as e:
                    print("stopped for "+str(e))
                    break

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

            self.gameplay()

        self.wait(10)

    def gameplay(self):
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

    def movement_loop(self):
        while True:
            if self.active:
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
            vel = [0, 0]
            vel[0] = cos(self.move_direction) * self.move_speed
            vel[1] = sin(self.move_direction) * self.move_speed

            if vel[0]:
                if vel[0] < 0:
                    self.motors[0].polarity = "normal"
                    self.motors[2].polarity = "inversed"
                    self.motors[0].run_forever(speed_sp=abs(vel[0]))
                    self.motors[2].run_forever(speed_sp=abs(vel[0]))
                elif vel[0] > 0:
                    self.motors[0].polarity = "inversed"
                    self.motors[2].polarity = "normal"
                    self.motors[0].run_forever(speed_sp=vel[0])
                    self.motors[2].run_forever(speed_sp=vel[0])
            if vel[1]:
                if vel[1] < 0:
                    self.motors[1].polarity = "normal"
                    self.motors[3].polarity = "inversed"
                    self.motors[1].run_forever(speed_sp=abs(vel[1]))
                    self.motors[3].run_forever(speed_sp=abs(vel[1]))
                elif vel[1] > 0:
                    self.motors[1].polarity = "inversed"
                    self.motors[3].polarity = "normal"
                    self.motors[1].run_forever(speed_sp=vel[1])
                    self.motors[3].run_forever(speed_sp=vel[1])

        if not self.active:
            self.stop_all_motors()
            return
        
        sleep(.01)

if __name__ == "__main__":
    robot = Robot()
    robot.run()