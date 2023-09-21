#!/usr/bin/env python3

MOTORS = 0xA1
SENSORS = 0xA2
LOCALHOST = 0xA3
DEBUG = None

import threading, json, socket
from time import sleep
from os.path import join, dirname
from math import pi, cos, sin, radians

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3, INPUT_4
if DEBUG in (SENSORS, None):
    from sensor import IRSeeker360

PORTS = {
    "MOTORS":   [OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D],
    "COMPASS":   INPUT_3,
    "IR":        INPUT_4
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
        self.command = "END-CAL"

class Robot:
    def __init__(self):
        """RoboCup Soccer Robot"""

        if DEBUG == None:
            self.motors = self.motors_init()

            self.compass_sensor = CompassSensor(PORTS["COMPASS"])
            self.ir_sensor = IRSeeker360(PORTS["IR"])

        elif DEBUG == MOTORS:
            self.motors = self.motors_init()

        elif DEBUG == SENSORS:
            self.compass_sensor = CompassSensor(PORTS["COMPASS"])
            self.ir_sensor = IRSeeker360(PORTS["IR"])
        
        else: raise Exception("Debug mode must be None, MOTORS, or SENSORS.")

        self.orientation = 0
        self.original_orientation = 0

        self.move_direction = None
        self.move_speed = MAX_SPEED

        self.see_ball = False
        self.global_ball_angle = None

        self.detection_extent = radians(31)

        self.active = False
        self.tick = 0

        # Client initialisation
        data = json.load(open(join(dirname(__file__), "./options.json")))
        self.target_host = data["host_address"]
        self.target_port = data["host_port"]
        self.client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.client.settimeout(2)

    def motors_init(self):
        """Initialise motors. Returns list of four motors."""
        return [
            Motor(PORTS["MOTORS"][0]),                     # LEFT    [0]
            Motor(PORTS["MOTORS"][1], polarity_bias=-1),   # FRONT   [1]
            Motor(PORTS["MOTORS"][2], polarity_bias=-1),   # RIGHT   [2]
            Motor(PORTS["MOTORS"][3])                      # BACK    [3]
        ]

    def move(self, angle, speed=None):
        """Set move direction and speed of robot"""

        if angle != None:
            self.move_direction = (angle - self.orientation) % (2*pi)
        if speed:
            self.move_speed = speed

    def stop(self):
        """Set move direction to None"""

        self.move_direction = None

    def wait(self, secs: int):
        """sleep(ms) and tick(secs)"""

        sleep(secs * .001)
        self.tick += secs

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
        """Start threads for robot; updates, movement, and requests."""

        threads = [
            threading.Thread(target=self.start_server),
            threading.Thread(target=self.update_loop),
            threading.Thread(target=self.movement_loop),
            threading.Thread(target=self.request_handler)
        ]

        for t in threads:
            t.start()

        print("run()")

    def start_server(self):
        print("start_server()")

        self.client.connect((self.target_host, self.target_port))
        print("Connected on " + str(self.client.getsockname()))

    def request_handler(self):
        """Handle requests from server"""
        
        print("request_handler()")

        while True:
            try:
                request = self.client.recv(16)
                if request:
                    self.process_request(request.decode())
            except TimeoutError: pass
            except ConnectionResetError: break
            except: raise

            sleep(0.01)

        print("Disconnected from server, closing client..")
        self.client.close()

    def process_request(self, request: str):
        """Process requests from server into callables. `request` parameter must be a string and is received by the server.
        Commands include: `set_speed value`, `set_state bool`, `move dir speed`, `reorientate`."""
        content = request.split()
        if len(content) >= 2:
            command = content[0]
            value = content[1]
            if command == "set_speed":
                self.move_speed = MAX_SPEED * float(value)
            elif command == "set_state":
                self.active = bool(int(value))
            elif command == "move":
                angle = float(content[1])
                speed = float(content[2])
                self.move(angle=angle, speed=MAX_SPEED * speed)
            else:
                self.client.send(request.encode())
        else:
            if "reorientate" in content:
                self.original_orientation = self.orientation
            elif "manual_stop" in content:
                if not self.active:
                    self.stop()

    def update_loop(self):
        """Update loop handling sensor values and gameplay logic."""
        if DEBUG == MOTORS:
            return
        
        print("update_loop()")
        self.original_orientation = radians(self.compass_sensor.value()) % (2*pi)

        while True:
            if self.active:
                try:
                    self.update()
                except Exception as e:
                    print("stopped for "+str(e))
                    break

                self.wait(10)

        print("Stopping")
        self.ir_sensor.close()

    def update(self):
        """Fixed update for getting sensor values and gameplay logic."""
        if (self.tick % 20) == 0:
            self.compass_sensor.angle = self.compass_sensor.value()
            self.orientation = (radians(self.compass_sensor.angle) - self.original_orientation) % (2*pi)

            self.relative_ball_angle, self.ball_strength = self.ir_sensor.read()
            self.relative_ball_angle_radians = (self.relative_ball_angle % 12) * pi/6
            self.global_ball_angle = (self.relative_ball_angle_radians + self.orientation) % (2*pi)
            
            self.see_ball = False
            if self.ball_strength > 1:
                self.see_ball = True

            self.gameplay()

            # for x in [self.ir_sensor.]
            # self.client.send()

    def gameplay(self): 
        """Gameplay logic"""
        if self.global_ball_angle > 3*pi/2 or self.global_ball_angle < pi/2:

            if self.ball_strength > 80:
                self.move(0)
            else:
                if self.global_ball_angle > 2*pi-self.detection_extent or self.global_ball_angle < self.detection_extent:
                    self.move(0)
                else:
                    if self.global_ball_angle < pi:
                        self.move(pi/2)
                    else:
                        self.move(3*pi/2)

        else:
            if self.global_ball_angle > pi - .3 and self.global_ball_angle < pi + .3:
                self.move(3*pi/2)
            else:
                self.move(pi)

    def movement_loop(self):
        """Movement thread handling movement."""

        print("movement_loop()")
        while True:
            self.movement()
            sleep(.01)

    def stop_all_motors(self):
        """Stops all motors."""
        self.motors[0].stop()
        self.motors[1].stop()
        self.motors[2].stop()
        self.motors[3].stop()

    def movement(self):
        """Fixed update for movement: rotating or stopping motors."""
        if DEBUG == SENSORS:
            return

        if self.move_direction == None or self.move_speed == None:
            self.stop_all_motors()
        else:
            vel = [cos(self.move_direction) * self.move_speed, sin(self.move_direction) * self.move_speed]

            if vel[0]:
                self.motors[0].run(vel[0])
                self.motors[2].run(vel[0])
            if vel[1]:
                self.motors[1].run(vel[1])
                self.motors[3].run(vel[1])

        # if not self.active:
        #     self.stop_all_motors()

if __name__ == "__main__":
    if DEBUG == LOCALHOST:
        data = json.load(open(join(dirname(__file__), "./options.json")))
        target_host = data["host_address"]
        target_port = data["host_port"]

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)

        try: client.connect(('127.0.0.1', 8080))
        except TimeoutError: raise Exception("Cannot connect..")
        except: raise
        print("Connected on " + str(client.getsockname()))

        def request_handler():
            while True:
                try:
                    request = client.recv(16) # max string of 16 chars
                    if request:
                        print(request.decode())
                except TimeoutError: pass
                except ConnectionResetError: break
                except: raise

                sleep(0.01)

            print("Disconnected from server, closing client..")
            client.close()


        request_handler()
    else:
        robot = Robot()
        robot.run()