import pygame, sys
from pygame.locals import *
from math import atan2, sqrt, radians, sin, cos

pygame.init()

screen = pygame.display.set_mode((800, 600))
ss = screen.get_size()
clock = pygame.time.Clock()

def draw_rotated_rect(rect, rotation):
    points = [
        (rect[2]/2, rect[3]/2),
        (rect[2]/2, -rect[3]/2),
        (-rect[2]/2, -rect[3]/2),
        (-rect[2]/2, rect[3]/2)
    ]
    l = sqrt((rect[2]/2)**2 + (rect[3]/2)**2)
    for i, p in enumerate(points):
        px = p[0]; py = p[1]
        r = atan2(py, px)
        points[i] = (rect[0] + cos(r + rotation) * l, rect[1] + sin(r + rotation) * l)
    
    for i in range(4):
        pygame.draw.line(screen, (255, 255, 255), points[i-1], points[i])

    return points

angle = 0

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    screen.fill("#313131")

    angle += .01
    draw_rotated_rect((300, 400, 140, 60), angle)
    pygame.draw.circle(screen, (255, 0, 100), (500, 170), 30, width = 3)

    p = [cos(angle)*150, sin(angle)*150]
    pygame.draw.line(screen, (255, 255, 0), (300, 400), (300+p[0], 400+p[1]))
    a = radians(90)-angle
    p = [cos(a)*150, sin(a)*150]
    pygame.draw.line(screen, (255, 0, 0), (300, 400), (300+p[0], 400+p[1]))
    pygame.draw.line(screen, (255, 100, 0), (300, 400), (300, 150))

    pygame.display.flip()
    clock.tick(60)