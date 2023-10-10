import pygame, sys
from pygame.locals import *
from math import sin, cos, sqrt, atan2, pi, log10
from random import randint

pygame.init()
screen = pygame.display.set_mode((1300, 800))
ss = screen.get_size()
clock = pygame.time.Clock()

SCROLL_DRAG = .08
CHECKER_SIZE = 40

TARGET_FPS = 30

WASD = 0x053
INDIVIDUAL = 0x054
DESTINATION = 0x055
AUTO = 0x056
modes = [WASD, INDIVIDUAL, DESTINATION, AUTO]
movement_mode = AUTO
mode_str = "wasd, individual motors, mouse, automatic".split(", ")
current_mode = mode_str[modes.index(movement_mode)]

LOCALS = locals()

def step_movement_mode():
    global movement_mode
    movement_mode = modes[(modes.index(movement_mode) + 1) % len(modes)]

def draw_rotated_rect(rect, rotation, color):
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
        pygame.draw.aaline(screen, color, points[i-1], points[i])

    return points

class IRSensor:
    def __init__(self, position, direction=0, view_distance=500, show_view_field=True):
        self.position = position
        self.view_distance = view_distance
        self.update(direction - pi/2)
        self.surf = pygame.Surface(ss)
        self.surf.set_colorkey((0, 0, 0))
        self.surf.set_alpha(25)

        self.show_view_field = show_view_field

        self.see_ball = False
        self.ball_dir = self.ball_strength = 0

    def update(self, direction=0, ball_pos=None):
        spread = 1.7
        self.left_bound = direction - spread
        self.right_bound = direction + spread

        self.see_ball = False
        self.ball_dir = self.ball_strength = 0
        if ball_pos:
            self.ball_dir = atan2(ball_pos[1] - self.position[1], ball_pos[0] - self.position[0])
            self.ball_strength = sqrt((ball_pos[1] - self.position[1])**2 + (ball_pos[0] - self.position[0])**2) / self.view_distance * 100
            if self.ball_dir >= self.left_bound and self.ball_dir <= self.right_bound and self.ball_strength <= 100:
                self.see_ball = True

    def read(self):
        if self.see_ball:
            return int((self.ball_dir - self.left_bound)/(self.right_bound - self.left_bound)*9 + 1), int(self.ball_strength)
        else:
            return 0, 0

    def draw(self, size=(8, 15)):
        draw_rotated_rect((self.position[0] - scroll[0], self.position[1] - scroll[1], size[0], size[1]), (self.left_bound + self.right_bound)/2 - pi/2, (255, 255, 255))
        
        if self.show_view_field:
            self.surf.fill("#000000")
            points = [self.position]
            n = 15
            for i in range(n):
                a = self.left_bound + i * (self.right_bound - self.left_bound) / (n-1)
                points.append((self.position[0] + cos(a) * self.view_distance, self.position[1] + sin(a) * self.view_distance))
            pygame.draw.polygon(self.surf, [(255, 180, 180), (230, 245, 180)][int(self.see_ball)], [[point[0] - scroll[0], point[1] - scroll[1]] for point in points])
            screen.blit(self.surf, (0, 0))

class Robot:
    def __init__(self, origin=(0, 0), orientation=0, target_speed=pi/50, radius=30):
        self.colors = [
            (255, 0, 0),
            (100, 150, 255),
            (150, 255, 155),
            (255, 255, 0)
        ]
   
        self.angular_vel = 0
        self.radius = radius

        self.origin = list(origin)
        self.vel = [0, 0]

        self.wheel_speed = 0
        self.speed = [0]*4
        self.target_speed = target_speed

        self.orientation = orientation

        self.position = [None]*4
        for i in range(4):
            ri = self.orientation + i * pi/2
            self.position[i] = [self.origin[0] - cos(ri) * self.radius, self.origin[1] - sin(ri) * self.radius]
        
        self.movement = "rftgyhuj"
        self.log = []
        self.lines = [[self.position[i]] for i in range(4)]
        self.show_trails = True

        self.hitbox = Polygon([(self.origin[0] + cos(a * pi/4 + pi/8) * self.radius * 1.1, self.origin[1] + sin(a * pi/4 + pi/8) * self.radius * 1.1) for a in range(8)])

        self.destination = None

        self.irs = [IRSensor((0, -10), direction=0), IRSensor((0, 10), direction=pi)]

    def move(self, rel_pos, rel_angle):
        direction = atan2(rel_pos[1], rel_pos[0])
        length = sqrt(rel_pos[0]**2 + rel_pos[1]**2)
        for i in range(4):
            self.speed[i] = (length * cos(self.orientation + i * pi/2 + direction - pi/2) + rel_angle) * self.wheel_speed

    def rotate_around(self, point1, point2, a):
        if point1 == point2:
            return point1
        length = sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
        angle = atan2(point1[1] - point2[1], point1[0] - point2[0]) + a
        return [point2[0] + length * cos(angle), point2[1] + length * sin(angle)]

    def draw(self):
        if self.show_trails:
            for i in range(4):
                if len(self.lines[i]) > 1:
                    pygame.draw.aalines(screen, self.colors[i], 0, [[l[0] - scroll[0], l[1] - scroll[1]] for l in self.lines[i]])
                if len(self.lines[i]) > 200:
                    self.lines[i].pop(0)

        for i in range(4):
            p = self.position[i]
            c = self.colors[i]
            draw_pos = [p[0] - scroll[0], p[1] - scroll[1]]
            pygame.draw.circle(screen, c, draw_pos, 2)
            point_angle = atan2(p[1] - self.origin[1], p[0] - self.origin[0])
            draw_rotated_rect((draw_pos[0], draw_pos[1], int(self.radius/4), self.radius), point_angle, c)

            if self.position[i] != self.lines[i][-1]:
                self.lines[i].append(self.position[i])
            self.position[i] = p
            
        pygame.draw.circle(screen, (255, 255, 255), (self.origin[0] - scroll[0], self.origin[1] - scroll[1]), self.radius, width=2)

        for i in range(4):
            pygame.draw.rect(screen, (100, 100, 100), (ss[0]-160, 10 * (i+1), 150, 2))
            if max(self.speed) != 0:
                pygame.draw.rect(screen, self.colors[i], (ss[0]-160, 10 * (i+1), self.speed[i]/max(self.speed)*150, 2))

        for i, line in enumerate(self.log):
            screen.blit(pygame.font.SysFont(None, 24).render(line[0], 1, line[1]), (10, 10 + i * 25))

        if movement_mode == INDIVIDUAL: screen.blit(pygame.font.SysFont(None, 24).render("Press r, t, y, u, f, g, h, or j for movement", 1, (255, 255, 255)), (10, ss[1]-25))
        if movement_mode == WASD: screen.blit(pygame.font.SysFont(None, 24).render("Press w, a, s, or d for movement", 1, (255, 255, 255)), (10, ss[1]-25))
        screen.blit(pygame.font.SysFont(None, 24).render("Press q to toggle trails", 1, (255, 255, 255)), (10, ss[1]-50))

        if self.destination:
            pygame.draw.circle(screen, (255, 0, 0), (self.destination[0] - scroll[0], self.destination[1] - scroll[1]), self.radius * (0.98 + .04 * sin(pygame.time.get_ticks() * .01)), 2)

        self.irs[0].draw()
        self.irs[1].draw()

    def calculate_wheels(self):
        for i in range(4):
            if self.speed[i]:
                rotate_point = self.position[(i+2) % 4]
                speed = self.speed[i]
                if speed:
                    for n in range(4):
                        self.position[n] = self.rotate_around(self.position[n], rotate_point, speed)

                    self.origin[0] = sum([x[0] for x in self.position])/4
                    self.origin[1] = sum([x[1] for x in self.position])/4

    def update(self, deltatime):
        self.wheel_speed = self.target_speed * deltatime
        self.orientation = atan2(self.position[2][1] - self.origin[1], self.position[2][0] - self.origin[0])

        k = pygame.key.get_pressed()

        if movement_mode == INDIVIDUAL:
            self.log.clear()
            for i in range(4):
                self.speed[i] = 0
            for i, key in enumerate(self.movement):
                n = int(i/2)
                direction = [1, -1][int(i % 2)]
                if k[LOCALS["K_"+key]]:
                    self.speed[n] = self.wheel_speed * direction * [1, -1][int(i >= 4)]
                    self.log.append(["Red Blue Green Yellow".split()[n] + " " + "forwards backwards".split()[int(i % 2)], self.colors[n]])

        elif movement_mode == WASD:
            
            if pygame.time.get_ticks() % randint(60, 100) == 0:
                self.angular_vel = randint(2, 5)
            else:
                self.angular_vel += (-self.orientation - self.angular_vel) * .05

            key_dir = [
                k[K_d] - k[K_a],
                k[K_w] - k[K_s]
            ]
            if key_dir[0] or key_dir[1]: self.move(key_dir, self.angular_vel)
            else: self.move((0, 0), self.angular_vel)

        if self.destination:
            if (self.destination[0] - self.origin[0])**2 + (self.destination[1] - self.origin[1])**2 <= (dt*2)**3:
                self.destination = None
            else:
                angle = -atan2(self.destination[1] - self.origin[1], self.destination[0] - self.origin[0])
                rel = [cos(angle), sin(angle)]
                self.move(rel, -self.orientation)
        old_pos = self.origin.copy()
        self.calculate_wheels()
        self.vel[0] = self.origin[0] - old_pos[0]
        self.vel[1] = self.origin[1] - old_pos[1]

        if not self.destination:
            for i in range(4):
                self.speed[i] = 0

        self.hitbox = Polygon([(self.origin[0] + cos(a * pi/4 + pi/8) * self.radius * 1.1, self.origin[1] + sin(a * pi/4 + pi/8) * self.radius * 1.1) for a in range(8)])

        self.irs[0].position = [self.origin[0], self.origin[1] - 10]
        self.irs[1].position = [self.origin[0], self.origin[1] + 10]
        self.irs[0].update(self.orientation - pi/2, ball.position)
        self.irs[1].update(self.orientation + pi/2, ball.position)

        robot.gameplay()

        self.draw()

    def average_two_angles_radians(self, a1, a2):
        d = ((a2 - a1 + pi/2) % (pi)) - pi/2
        return (a1 + d/2) % (pi)

    def gameplay(self):
        if movement_mode == AUTO:
            a1 = self.irs[0].read()[0] * pi / 9
            a2 = self.irs[1].read()[0] * pi / 9
            if a1 and a2:
                relative_ball_direction = self.average_two_angles_radians(a1, a2 + pi)
            elif a1 == 0:
                relative_ball_direction = a2
            elif a2 == 0:
                relative_ball_direction = a1 + pi
            else:
                relative_ball_direction = None
                return
            if relative_ball_direction:
                strength = max(self.irs[0].read()[1], self.irs[1].read()[1]) * 5

                relative_ball_direction = (relative_ball_direction + pi/2) % (2*pi)
                global_ball_direction = relative_ball_direction - self.orientation
                # if global_ball_direction < pi/3 or global_ball_direction >= pi + pi/3:
                #     if global_ball_direction < .2 or global_ball_direction >= 2*pi - .2:
                #         self.move((0, 1), 0)
                #     else:
                #         if global_ball_direction < pi:
                #             self.move((1, 0), 0)
                #         elif global_ball_direction >= pi:
                #             self.move((-1, 0), 0)
                # else:
                #     if global_ball_direction > pi - .4 and global_ball_direction <= pi + .74:
                #         self.move((-1, -1), 0)
                #     else:
                #         self.move((0, -1), 0)
                if global_ball_direction < .2 or global_ball_direction >= 2*pi - .2:
                    self.move((0, 1), 0)
                else:
                    if global_ball_direction < pi/3 or global_ball_direction >= pi + pi/3:
                        dest = [self.origin[0] + strength * cos(global_ball_direction - pi/2), self.origin[1] + strength * sin(global_ball_direction - pi/2) + 50]
                    else:
                        dest = [self.origin[0] + strength * cos(global_ball_direction - pi/2) - 50, self.origin[1] + strength * sin(global_ball_direction - pi/2) + 50]
                    if not self.destination:
                        self.destination = dest
                    else:
                        f = .9
                        self.destination[0] += (dest[0] - self.destination[0]) * f
                        self.destination[1] += (dest[1] - self.destination[1]) * f
            else:
                self.destination = None

class Line:
    def __init__(self, start, end):
        if start[0] > end[0]:
            self.start = end
            self.end = start
        else:
            self.start = start
            self.end = end

class Polygon:
    def __init__(self, points):
        self.points = points
        self.edges = [Line(point, self.points[(i-1) % len(self.points)]) for i, point in enumerate(self.points)]

    def draw(self, offset=(0, 0), color=(255, 255, 255)):
        pygame.draw.polygon(screen, color, [[point[0] + offset[0], point[1] + offset[1]] for point in self.points], 1)

class Ball:
    def __init__(self, position, radius, color=(220, 220, 255)):
        self.position = list(position)
        self.original_position = self.position.copy()
        self.radius = radius
        self.color = color

        self.vel = [0, 0]

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.position[0] - scroll[0], self.position[1] - scroll[1]), self.radius, 1)

    def collide_with_line(self, line: Line):
        sample_points = []
        samples = 16
        for i in range(samples):
            sample_points.append([line.start[0] + (line.end[0]-line.start[0]) * (i/samples), line.start[1] + (line.end[1]-line.start[1]) * (i/samples)])
        
        for point in sample_points:
            squared_dist = (point[0] - self.position[0])**2 + (point[1] - self.position[1])**2
            if squared_dist < self.radius**2 and squared_dist > self.radius**2*.8:
                return point

        return None

    def average(self, points):
        ax = sum([x[0] for x in points])/len(points)
        ay = sum([x[1] for x in points])/len(points)
        return [ax, ay]

    def collide_with_polygon(self, polygon: Polygon):
        xarr = [x[0] for x in polygon.points]
        yarr = [x[1] for x in polygon.points]
        left = min(xarr)
        top = min(yarr)
        right = max(xarr)
        bottom = max(yarr)
        rect = pygame.Rect(left, top, right-left, bottom-top)

        collisions = []
        if rect.colliderect(pygame.Rect(self.position[0] - self.radius, self.position[1] - self.radius, self.radius*2, self.radius*2)):
            for line in polygon.edges:
                collision = self.collide_with_line(line)
                if collision: collisions.append(collision)
        
        if collisions:
            average_collision = self.average(collisions)

            out_dir = atan2(self.position[1] - average_collision[1], self.position[0] - average_collision[0])
            out_speed = sqrt(robot.vel[0]**2 + robot.vel[1]**2) + sqrt((self.position[0] - average_collision[0])**2 + (self.position[1] - average_collision[1])**2) * .02
            
            self.vel[0] = out_speed * cos(out_dir)
            self.vel[1] = out_speed * sin(out_dir)

    def update(self, robot: Robot):
        self.draw()
        self.collide_with_polygon(robot.hitbox)
        self.position[0] += self.vel[0]
        self.position[1] += self.vel[1]
        coeff = .985 # log10(9.7 - min(.99, sqrt(self.vel[0]**2 + self.vel[1]**2)))
        self.vel[0] *= coeff
        self.vel[1] *= coeff

true_scroll = [-ss[0]//2, -ss[1]//2]
scroll = true_scroll.copy()

robot = Robot(origin=(0, 400), radius=30)
ball = Ball((0, 0), 40)
field = {"bounds": [-300, -500, 600, 1000], "goal_width": 200, "wall_width": 6, "goal_depth": 80, "bounciness": .5}
goal_1 = pygame.Rect(field["bounds"][0] + field["bounds"][2]//2 - field["goal_width"]//2, field["bounds"][1] - field["wall_width"], field["goal_width"], field["goal_depth"])
goal_2 = pygame.Rect(field["bounds"][0] + field["bounds"][2]//2 - field["goal_width"]//2, field["bounds"][1] + field["bounds"][3] + field["wall_width"] - field["goal_depth"], field["goal_width"], field["goal_depth"])

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_q:
                robot.show_trails = not robot.show_trails
            elif event.key == K_e:
                for i in range(2):
                    robot.irs[i].show_view_field = not robot.irs[i].show_view_field
            elif event.key == K_m:
                step_movement_mode()
                current_mode = mode_str[modes.index(movement_mode)]

    if movement_mode == DESTINATION:
        if pygame.mouse.get_pressed()[0]:
            robot.destination = [pygame.mouse.get_pos()[i] + scroll[i] for i in range(2)]

    screen.fill("#242424")

    dt = clock.tick(TARGET_FPS) * .06
    true_scroll = [robot.origin[0] - ss[0]//2, robot.origin[1] - ss[1]//2]
    scroll = [scroll[0] + (true_scroll[0] - scroll[0]) * SCROLL_DRAG * dt, scroll[1] + (true_scroll[1] - scroll[1]) * SCROLL_DRAG * dt]

    for y in range(0, ss[1] + CHECKER_SIZE*2, CHECKER_SIZE):
        for x in range(0, ss[0] + CHECKER_SIZE*2, CHECKER_SIZE):
            i = y//CHECKER_SIZE * (ss[0]//CHECKER_SIZE + 3) + x//CHECKER_SIZE
            c = 25 * int(i % 2 == 0)
            pygame.draw.rect(screen, [c]*3, (x - scroll[0]%(CHECKER_SIZE*2), y - scroll[1]%(CHECKER_SIZE*2), CHECKER_SIZE, CHECKER_SIZE))

    p1 = (max(0, int(field["bounds"][0] - scroll[0])), max(0, int(field["bounds"][1] - scroll[1])))
    p2 = (max(0, int(field["bounds"][0] - scroll[0]) + field["bounds"][2]), max(0, int(field["bounds"][1] - scroll[1]) + field["bounds"][3]))
    size = (abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))
    if not(size[0] == 0 or size[1] == 0):
        screen.fill((9, 18, 9), (p1[0], p1[1], size[0], size[1]), special_flags=BLEND_RGBA_ADD)
    pygame.draw.rect(screen, (237, 94, 17), pygame.Rect(pygame.Vector2(goal_1.topleft) - scroll, goal_1.size), 1, border_radius=5)
    pygame.draw.rect(screen, (50, 79, 186), pygame.Rect(pygame.Vector2(goal_2.topleft) - scroll, goal_2.size), 1, border_radius=5)
    pygame.draw.rect(screen, (48, 48, 48), (int(field["bounds"][0] - scroll[0] - field["wall_width"]), int(field["bounds"][1] - scroll[1] - field["wall_width"]), field["bounds"][2] + field["wall_width"]*2, field["bounds"][3] + field["wall_width"]*2), field["wall_width"], border_radius=20)

    robot.update(dt)
    ball.update(robot)
    if movement_mode == AUTO:
        if pygame.mouse.get_pressed()[0]:
            ball.position = [pygame.mouse.get_pos()[0] + scroll[0], pygame.mouse.get_pos()[1] + scroll[1]]

    if goal_1.collidepoint(ball.position):
        ball.position = ball.original_position.copy()
    
    if ball.position[0] > field["bounds"][0] + field["bounds"][2] - ball.radius or ball.position[0] < field["bounds"][0] + ball.radius:
        ball.position[0] -= ball.vel[0]
        ball.vel[0] *= -field["bounciness"]
    if ball.position[1] > field["bounds"][1] + field["bounds"][3] - ball.radius or ball.position[1] < field["bounds"][1] + ball.radius:
        ball.position[1] -= ball.vel[1]
        ball.vel[1] *= -field["bounciness"]

    text = pygame.font.SysFont(None, 24).render("Current Mode: "+current_mode.capitalize(), 1, (255, 255, 220))
    text_rect = text.get_rect(bottomright=(ss[0]-10, ss[1]-10))
    screen.blit(text, text_rect)

    pygame.display.flip()
    pygame.display.set_caption(f"FPS: {str(clock.get_fps())}")