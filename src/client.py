#!/usr/bin/env python3

"""
THE PROGRAM WHICH CONTROLS THE ROBOT; MUST BE RUN ON THE ROBOT OTHERWISE IT WONT WORK.
"""

from time import sleep
import socket, sys, threading, json
from os.path import join, dirname
from random import randint
from math import pi, cos, sin, atan2

from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_2, INPUT_3
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from ev3dev2.led import Leds

from sensor import IRSeeker360

# Initalise sensors
leds = Leds()

MOTORS = 0
SENSORS = 1
mode = MOTORS

MANUAL = 0
AUTOMATIC = 1
movement_mode = MANUAL

ATTACK = 0
DEFENSE = 1
current_strat = ATTACK

sensor = IRSeeker360(INPUT_1)

motors = None
gyroscope = gyro_angle = None
colour_sensor = sensed_colour = None
ts = None
can_press = False
if mode == MOTORS:
    motors = [
        MediumMotor(OUTPUT_A), # FRONT  [0]
        MediumMotor(OUTPUT_B), # RIGHT  [1]
        MediumMotor(OUTPUT_C), # BACK   [2]
        MediumMotor(OUTPUT_D)  # LEFT   [3]
    ]
    compass = Sensor(driver_name="ht-nxt-compass", address=INPUT_2)
    compass.mode = "COMPASS"
    compass_angle = 0
    
elif mode == SENSORS:
    ts = TouchSensor(INPUT_1)
    gyroscope = Sensor(driver_name="ht-nxt-compass", address=INPUT_2)
    gyroscope.mode = "COMPASS"
    gyro_angle = 0
    original_angle = gyroscope.value()

    colour_sensor = ColorSensor(INPUT_3)
    sensed_colour = None

# Connect to server
data = json.load(open(join(dirname(__file__), "./options.json")))
target_host = data["host_address"]
"""
This is my bluetooth address for the connection adapter thingy,
You can find yours when you connect the EV3 and the laptop, then open
command prompt, type in 'ipconfig /all', find the one that says bluetooth,
then copy the Physical Address. Make sure to replace - with :
"""
target_port = data["host_port"] # Abitrary port number, could use any port honestly

client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
client.settimeout(1)

client.connect((target_host, target_port))

# The old ping-pong requests to make sure both the client and server can send and receive.
response = client.recv(1024)
if response.decode() == "ping":
    print("Successful")
else:
    print("Not successful")

client.send("pong".encode())

pos = [0, 0]
vel = [0, 0]
angle = strength = None

def main_():
    """Main loop which controls the button press, and getting the compass and colour sensor values."""
    global gyro_angle, sensed_colour, angle, strength, vel, pos, compass_angle, angle, strength, can_press, motors
    while True:
        # Button logic
        if mode == SENSORS:
            if ts.is_pressed:
                if can_press:
                    client.send("a msg {}".format(str(randint(0, 4381))).encode())
                    can_press = False
            else:
                can_press = True

            # Get the gyroscope and colour sensor values into variables
            gyro_angle = gyroscope.value() - original_angle
            sensed_colour = colour_sensor.rgb

        if mode == MOTORS:
            compass_angle = compass.value()
            print(movement_mode)
            if movement_mode == AUTOMATIC:
                if current_strat == ATTACK:
                    angle, strength = sensor.read()
                    a = (angle % 12) * pi/6 #+ (compass_angle * pi/180) #+ pi/4
                    vel = [cos(a)*720, sin(a)*720]
                elif current_strat == DEFENSE:
                    vel[0] = pos[0]/10
                    vel[1] = pos[1]/10

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
            pos[0] += vel[0]
            pos[1] += vel[1]

        sleep(0.01)

def receive():
    global vel, movement_mode, current_strat, client, leds, mode, movement_mode
    """Deals with most of the requests from the server connection. It sends the values over to the server to show on the GUI"""
    while True:
        try:
            request = client.recv(1024) # Get request from socket connection
            if request:
                r = request.decode()
                if "change_movement_mode" in r:
                    movement_mode = (MANUAL, AUTOMATIC)[int(r[-1])]
                    client.send("movement_mode = {}".format(str(movement_mode)).encode())

                    # The change_movement_mode state thing controls this. Just controls the LED on the EV3 for now.
                    if movement_mode == AUTOMATIC:
                        leds.set_color('LEFT', 'AMBER')
                    elif movement_mode == MANUAL:
                        leds.reset()
                elif "change_strat" in r:
                    current_strat = int(r[-1])
                    client.send("current_strat = {}".format(str(current_strat)).encode())

                elif "move" in r:
                    # if movement_mode == MANUAL:
                    v = [round(float(x), 1) for x in r.split()[1].split(",")]
                    a = atan2(v[1], v[0]) # compass correction
                    a -= (compass_angle) * pi/180
                    vel = [round(cos(a)*720, 1), round(sin(a)*720, 1)]
                        # client.send(("debug "+str(vel)).encode())

            else: break # End loop if the server has closed.
        except Exception as e:
            raise e

        # Finally sending the values to the server to be processed.
        if mode == SENSORS:
            if gyro_angle:
                client.send("gyro_angle {}".format(str(gyro_angle)).encode())
            if sensed_colour:
                client.send("sensed_colour {}".format(str(sensed_colour)).encode())

        if movement_mode == AUTOMATIC:
            client.send((str(angle) + ", " + str(strength)).encode())

        sleep(0.01)

    sys.exit()

"""Just running both the main() and receive() loops asynchronously with multithreading."""
threads = [
    threading.Thread(target=main_),
    threading.Thread(target=receive)
]

for t in threads:
    t.start()

for t in threads:
    t.join()

sensor.close()