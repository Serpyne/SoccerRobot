import pygame, sys
from pygame.locals import *
from math import pi, sin, cos, radians, sqrt, atan2

pygame.init()
screen = pygame.display.set_mode((800, 600))
ss = screen.get_size()
clock = pygame.time.Clock()

class Vector:
    def __init__(self, x=0, y=0, magnitude=None, direction=None):
        if magnitude and direction:
            m = __import__("math")
            self.x = magnitude * m.cos(direction)
            self.y = magnitude * m.sin(direction)
        else:
            self.x: float = x
            self.y: float = y
    @classmethod
    def from_xy(self, x: float, y: float):
        v = Vector(x=x, y=y)
        return v
    @classmethod
    def from_dir(self, direction: float, magnitude: float):
        v = Vector(magnitude=magnitude, direction=direction)
        return v
    def __str__(self) -> str:
        return "(%s, %s)" % (str(self.x), str(self.y))
    def __add__(self, vec):
        if type(vec) == Vector:
            return (self.x + vec.x, self.y + vec.y)
        elif type(vec) in (tuple, list):
            return (self.x + vec[0], self.y + vec[1])

def rotate(center, size, degrees, rot_offset=0):
    if rot_offset:
        t = (center[0] + size[0]/2 * cos(radians(degrees)), center[1] + size[1]/2 * sin(radians(degrees)))
        mag = sqrt((t[0] - center[0])**2 + (t[1] - center[1])**2)
        r = atan2((t[1] - center[1]), (t[0] - center[0])) + radians(rot_offset)
        v = (mag * cos(r) + center[0], mag * sin(r) + center[1])
        return v
    else:
        return (center[0] + size[0]/2 * cos(radians(degrees)), center[1] + size[1]/2 * sin(radians(degrees)))

def draw_circle(center, size, rotation, color=(255, 255, 255)):
    points = []
    for r in range(0, 360, 5):
        points.append(rotate(center, size, r, rot_offset=rotation))
    pygame.draw.lines(screen, color, closed=1, points=points, width=1)

def draw_wheel(center, size, rotation, angle, color=(255, 255, 255)):
    pygame.draw.line(screen, color, center, rotate(center, size, angle, rot_offset=rotation))
    draw_circle(center, size, rotation=rotation)

angle = [0, 0, 180, 180]
direction = 0
speed = 5

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((51, 51, 51))
    pygame.draw.polygon(screen, (205, 159, 59), ((400, 50), (400, 400), (300, 320)))
    pygame.draw.polygon(screen, (205, 159, 59), ((400, 50), (400, 400), (500, 320)))
    pygame.draw.line(screen, (130, 120, 59), (400, 50), (400, 400))

    m = pygame.mouse.get_pos()
    direction = atan2(m[1] - 300, m[0] - 400)
    pygame.draw.line(screen, (255, 0, 0), (400, 300), rotate((400, 300), (100, 100), direction*180/pi))

    real_dir = -direction + pi/4
    angle[0] += cos(real_dir) * speed  # top right
    angle[1] += sin(real_dir) * speed  # bottom right
    angle[2] += cos(real_dir) * speed  # bottom left
    angle[3] += sin(real_dir) * speed  # top left

    for i, a in enumerate(angle):
        angle[i] = a % 360

    for i in range(4):
        t = [50, 0, 0, 50][i]
        draw_wheel(rotate((400, 300+t/2), (400, 400), i*90 - 45), (300-t, 150-t), 45 + i*90, angle[i], (255, 200, i/4*255))

    screen.blit(pygame.font.SysFont(None, 33).render(str(round(direction*180/pi, 2)), 1, (255, 255, 255)), (20, 20))
    for i in range(4):
        v = str(round(angle[i], 2))
        screen.blit(pygame.font.SysFont(None, 33).render(v, 1, (255, 255, 255)), (20, 60 + i*30))

    pygame.display.flip()
    clock.tick(60)