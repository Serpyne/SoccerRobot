from math import atan2, sqrt, cos, sin, pi
from ev3dev2.motor import MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D



motors = [MediumMotor(OUTPUT_A),MediumMotor(OUTPUT_B), MediumMotor(OUTPUT_C), MediumMotor(OUTPUT_D)]

orientation = -pi/4

def move(rel_pos, rel_angle):

    norm = max(rel_pos[0], rel_pos[1])
    rel_pos = [rel_pos[0]/norm, rel_pos[1]/norm]


    direction = atan2(rel_pos[1], rel_pos[0])
    length = sqrt(rel_pos[0]**2 + rel_pos[1]**2)

    speeds = []

    for i in range(4):
        speed = round(length * cos(orientation + pi/2 * (i - 1) + direction) + rel_angle / (2*pi), 3)
        speeds.append(speed)
    
    max_speed = max(speeds)
    speeds = [speed/max_speed for speed in speeds]

    for i, motor in enumerate(motors):
        motor.run_forever(speed_sp=1560 * speeds[i])



move((1, 1), pi/4)