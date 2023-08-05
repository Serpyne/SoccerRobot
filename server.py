"""
THE SERVER AND GUI/CONTROLLER
"""

import socket, sys, time
import threading
from tkinter import *
from tkinter import font, Frame
from math import sin, cos, pi, sqrt, atan2, radians, degrees
from json import load, dump
from os.path import join, dirname

def rgb_to_hex(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code"""
    return "#%02x%02x%02x" % rgb   

def cerp(y1, y2, step):
    """Short for Cosine Interpolation. Just to smooth out the animations"""
    t = (1 - cos(step * pi))/2
    return y1 * (1-t) + (y2-50) * t

def lerp(y1, y2, step):
    """Short for Linear Interpolation. Just to smooth out the animations"""
    return y1 + (y2 - y1) * step

def filename(path):
    return join(dirname(__file__), path)

class Server:
    """Server which handles requests and sends things"""
    def __init__(self, root: Tk, host_addr, port, active=True):
        self.root = root

        self.host_addr = host_addr # Replace this with your own IP address
        self.port = port # Feel free to change this port
        
        self.backlog = 1
        self.size = 1024

        self.ready = False

        if active:
            self.server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.server.bind((self.host_addr, self.port))
            self.server.listen(self.backlog)
            print("Server is listening on %s:%d" % (self.host_addr, self.port))

        self.gyro_angle = None
        self.sensed_colour = None

    def clientHandler(self, client_socket): # MOST IMPORTANT FUNCTION. HANDLES SERVER AND CLIENT REQUESTS.
        try:
            client_socket.send("ping".encode())

            request = client_socket.recv(self.size)
            if request.decode() == "pong":
                print("Connection established")
                self.ready = True

            while True:
                request = client_socket.recv(self.size)
                if request:
                    r = request.decode()
                    if len(r.split()) <= 2:
                        if r == "quit": break
                        elif "gyro_angle" in r:
                            self.gyro_angle = int(r.split()[1])
                        elif "sensed_colour" in r:
                            l = r.split()[1:]
                            colour = " ".join(l)
                            self.sensed_colour = [int(x) for x in "".join(list(str(colour))[1:-1]).split(", ")]
                        else: print(r)
                        data = {
                            "gyro_angle": self.gyro_angle,
                            "sensed_colour": self.sensed_colour
                        }
                        self.root.update_(data)
                    else: print(r)

            print("Closing socket 1")
            client_socket.close()
            self.server.close()
        except Exception as e:
            # client_socket.close()
            # self.server.close()
            raise e
            pass

    def send_packets(self, client_socket):
        while True:
            try:
                if self.ready:
                    # print("move " + self.root.movement_str)
                    client_socket.send(("move " + self.root.movement_str).encode())
            except Exception as e:
                raise e
            
            time.sleep(0.1)

    def start(self):
        self.client, addr = self.server.accept()
        print("Client connected " + str(addr))

        client_handler = threading.Thread(target = self.clientHandler, args=(self.client,))
        client_handler.start()
        client_sender = threading.Thread(target = self.send_packets, args=(self.client,))
        client_sender.start()

class Toggle:
    """Like a switch on-off button if we ever need different modes for the bot, or if we need it to say, run backwards for a desired amount of time."""
    def __init__(self, root, position, size, cursor_radius=20, state=0, command=None):
        self.root = root

        self.command = command

        self.width = 0
        self.count = 0
        
        self.pos = tuple(position)
        self.size = tuple(size)
        self.cursor_radius = cursor_radius

        self.state = bool(state)
        self.interval = 8

        # the actual image of the button
        self.canvas = Canvas(self.root, background=self.root.colour, height=self.size[1], width=self.size[0], bd=0, relief='ridge', highlightthickness=0)
        self.draw()      
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.place(x=self.pos[0], y=self.pos[1])

    def draw(self):
        """Drawing the image of the button onto the canvas widget"""
        r = (1 - self.width/self.size[0])*255
        g = (self.width/self.size[0])*255
        c = rgb_to_hex((int(r), int(g), 0))
        self.canvas.delete("all")
        self.canvas.create_rectangle(self.size[1]/2, 0, self.size[0]-self.size[1]/2, self.size[1], fill=c, outline="")
        self.canvas.create_arc(0, 0, self.size[1], self.size[1]-1, fill=c, outline="", start=90, extent=180)
        self.canvas.create_arc(self.size[0]-self.size[1], self.size[1]-1, self.size[0], 0, fill=c, outline="", start=270, extent=180)
        rx = self.size[1]/2 - self.cursor_radius
        ry = self.size[1]/2 + self.cursor_radius
        self.canvas.create_oval(self.width + rx, rx, ry+self.width, ry, fill="white", outline="")

    def click(self, *args):
        """The inital click function"""
        self.state = (self.state + 1) % 2
        msg = "{} {}".format(self.command, str(self.state))
        if self.command and self.root.main.debug_mode == 0:
            self.root.server.client.send(msg.encode())
        if self.root.main.debug_mode:
            print(msg)
        self.animate()

    def animate(self):
        """What runs after the .click() function to make it look nice and smooth (definitely necessary to boost team moral)"""
        if self.count < self.size[0] - self.size[1]:
            self.count = cerp(self.count, self.size[0]+1, .3)
            if self.state:
                self.width = cerp(self.width, self.size[0]+1, .3)
            else:
                self.width = self.size[0] - self.size[1] - self.count
            self.draw()
            self.root.after(self.interval, self.animate)
        else:
            self.count = 0

class Container(Frame):
    def __init__(self, root, *args, **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.colour = root.colour

class Main(Tk):
    """Manager for frames"""
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.wm_title("Robot GUI")
        self.colour = rgb_to_hex((55, 55, 55))
        self.config(bg=self.colour)
        self.size = (1280, 720)
        self.geometry("x".join([str(x) for x in self.size]))

        self.debug_mode = 0
        
        container = Frame(self, bg=self.colour) 
        container.pack(side = "top", fill = "both", expand = True)
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        self.frames = {"main": None, "calibrate_wheels": None}

        self.frames["main"] = StartFrame(container, self, bg=self.colour)
        self.frames["calibrate_wheels"] = CalibrateWheelsMenu(container, self, bg=self.colour)

        for f in self.frames:
            self.frames[f].grid(row = 0, column = 0, sticky ="nsew")

        self.show_frame("main")

    def show_frame(self, k):
        self.frames[k].tkraise()

options = load(open(filename("options.json"), "r"))
host_address = options["host_address"]
host_port = options["host_port"]

class StartFrame(Frame):
    """The actual GUI of the whole thing, parent of the server and UI elements."""
    def __init__(self, root, main, *args, **kwargs):
        Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.main = main
        self.colour = self.main.colour
        
        self.angle = 0
        self.new_angle = 0

        self.movement_str = "0.0,0.0"

        if self.main.debug_mode == 0:
            # Starting server. Made my own Server class at the top of the file.
            self.server = Server(self, host_addr=host_address, port=host_port)
            self.server.start()
        else:
            self.server = Server(self, host_addr=host_address, port=host_port, active=False)
            self.server.gyro_angle = 170

        # UI
        f1 = font.Font(family="Verdana", size=28, weight="bold", underline=1)
        Label(self, font=f1, bg=self.colour, fg="white", text="Robot GUI").pack()

        f2 = font.Font(family="Verdana", size=18)
        Label(self, font=f2, bg=self.colour, fg="white", text="MANUAL/AUTOMATIC").place(x=20, y=80)
        
        f2 = font.Font(family="Verdana", size=18)
        Label(self, font=f2, bg=self.colour, fg="white", text="ATTACK/DEFENSE").place(x=20, y=155)
        
        f3 = font.Font(family="Verdana", size=7, weight="bold")
        self.angle_canvas = Canvas(self, bg=rgb_to_hex((70, 70, 70)), height=200, width=200, bd=0, relief='ridge', highlightthickness=0)
        self.angle_canvas.place(x=30, y=300)
        self.gyro_angle_label = Label(self, font=f3, bg=rgb_to_hex((70, 70, 70)), fg="white", text="Gyro Angle: N/A")
        self.gyro_angle_label.place(x=30, y=300)

        self.colour_canvas = Canvas(self, bg="white", height=200, width=200, bd=0, relief='ridge', highlightthickness=0)
        self.colour_canvas.place(x=300, y=300)
        self.sensed_colour_label = Label(self, font=f3, bg="white", fg="white", text="Sensed Colour: N/A")
        self.sensed_colour_label.place(x=300, y=300)

        if self.main.debug_mode:
            self.update_({"gyro_angle": 170, "sensed_colour": (49, 150, 210)})
        
        self.toggle = Toggle(self, position=(310, 75), size=(130, 50), command="change_movement_mode")
        self.change_strat_toggle = Toggle(self, position=(310, 150), size=(130, 50), command="change_strat")
        self.calibration_menu_button = Button(self, text="Calibrate wheels MENU", command=lambda: self.main.show_frame("calibrate_wheels"))
        self.calibration_menu_button.pack()

        self.js = Joystick(self, position=(870, 10), size=(400, 380), center=(320, 300), radius=70, cursor_radius=20, bg=rgb_to_hex((70, 70, 70)))
        self.calibration_js = Joystick(self, text="Calibration", position=(970, 400), size=(300, 300), center=(150, 150), radius=120, cursor_radius=30, bg=self.colour, mode="stiff")
        self.js.loop()
        self.calibration_js.loop()
        try:
            self.calibration_js.angle = radians(self.server.gyro_angle)
        except: pass

        self.loop_()

    def update_(self, data):
        """Updates the labels and canvases"""
        self.new_angle = data["gyro_angle"]
        self.gyro_angle_label.config(text="Gyro Angle: " + str(self.new_angle))
        if data["sensed_colour"]:
            colour = rgb_to_hex(tuple(data["sensed_colour"]))
            self.sensed_colour_label.config(text="Sensed Colour: " + str(data["sensed_colour"]), bg=colour)
            self.colour_canvas.config(bg=colour)

    def loop_(self):
        """I didn't like the arrow of the gyroscope canvas just immediately moving, so I added some linear interpolation. Just a nice touch :)"""
        self.angle = (lerp(self.angle, self.new_angle, .1))
        dest = [
            100 * (1 + .8 * cos(self.angle * pi / 180)),
            100 * (1 + .8 * sin(self.angle * pi / 180))
        ]
        self.angle_canvas.delete("all")
        self.angle_canvas.create_line(100, 100, dest[0], dest[1], arrow="last", width=1)

        self.js.r = self.calibration_js.angle
        # print("Bot angle: {}; Joystick direction: {}; Moving direction: {}".format(str(round(degrees(self.js.r)) % 360), str(round(degrees(self.js.angle)) % 360), str(round(degrees(self.js.angle + self.js.r)) % 360)))
        speed = 720
        t = round(self.js.rot[0]*speed, 1), round(self.js.rot[1]*speed, 1)
        if t[0] != 0 and t[1] != 0:
            self.movement_str = str(t[0]) + "," + str(t[1])

        self.after(16, self.loop_)

class CalibrateWheelsMenu(Frame):
    """The actual GUI of the whole thing, parent of the server and UI elements."""
    def __init__(self, root, main, *args, **kwargs):
        Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.main = main
        self.colour = self.main.colour

        # UI
        f1 = font.Font(family="Verdana", size=28, weight="bold", underline=1)
        Label(self, font=f1, bg=self.colour, fg="white", text="Calibrate Wheels").pack()

        self.toggles = []

        f2 = font.Font(family="Verdana", size=18)
        for i in range(4):
            Label(self, font=f2, bg=self.colour, fg="white", text="Motor "+str(i+1)).place(x=500, y=130+i*60)
            self.toggles.append(Toggle(self, position=(700, 125+i*60), size=(110, 40), cursor_radius=12, command="calibrate_motor_"+str(i+1)))


        self.go_back_button = Button(self, text="Go back", command=lambda: self.main.show_frame("main"))
        self.go_back_button.pack()

        self.loop_()

    def update_(self, data):
        pass

    def loop_(self):
        self.after(16, self.loop_)

def rotate(point, origin=(0,0), rot=0):
    mag = sqrt((point[0]-origin[0])**2 + (point[1]-origin[1])**2)
    a = atan2(point[1]-origin[1], point[0]-origin[0])
    vx = mag * cos(rot + a)
    vy = mag * sin(rot + a)
    return [vx + origin[0], vy + origin[1]]

def draw_rotated_rect(canvas, center, size, rot, fill=None):
    points = [
        (size[0]/2, size[1]/2),
        (size[0]/2, -size[1]/2),
        (-size[0]/2, -size[1]/2),
        (-size[0]/2, size[1]/2)
    ]
    temp = [rotate(p, rot=rot) for p in points]
    points = []
    for p in temp:
        points.append(int(p[0] + center[0]))
        points.append(int(p[1] + center[1]))
    canvas.create_polygon(points, fill=fill, outline="black", width=5)
    return points

class Joystick:
    def __init__(self, root, position, size, center, radius, cursor_radius, fill="grey", cursor_colour="darkgrey", bg="white", mode="test", text=None):
        self.root = root
        self.mode = mode

        self.pos = [0, 0]
        self.new_pos = self.pos.copy()

        self.m = None
        self.r = 0
        self.car_pos = [200, 200]

        self.angle = 0

        self.center = center
        self.extent = radius
        self.cursor_rad = cursor_radius
        self.fill = fill
        self.cursor_colour = cursor_colour

        self.text = text

        self.cw = size[0]
        self.ch = size[1]
        self.canvas = Canvas(root, width=self.cw, height=self.ch, bg=bg, bd=0, relief='ridge', highlightthickness=0)
        self.canvas.place(x=position[0], y=position[1])

        self.l = Label(self.root, bg=bg)
        if self.text:
            self.l.config(text=str(self.text))
        self.l.place(x=position[0], y=position[1])

        self.canvas.bind('<B1-Motion>', self.press)
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<ButtonRelease-1>', self.release)

    def draw(self):
        self.canvas.delete('all')
        self.canvas.create_oval(
            (self.center[0] - self.extent, self.center[1] - self.extent, self.center[0] + self.extent, self.center[1] + self.extent), 
            fill=self.fill)
        self.canvas.create_oval(
            (self.center[0] - self.cursor_rad + self.pos[0], self.center[1] - self.cursor_rad + self.pos[1],
              self.center[0] + self.cursor_rad + self.pos[0], self.center[1] + self.cursor_rad + self.pos[1]),
            fill=self.cursor_colour)
        if self.m:
            t = [self.m[0] - self.center[0], self.m[1] - self.center[1]]
            if not(t[0]*t[0] + t[1]*t[1] < self.extent**2) or self.mode == "stiff":
                a = atan2(t[1], t[0])
                self.angle = a
                self.new_pos = [self.extent*cos(a), self.extent*sin(a)]
            else:
                self.new_pos = t.copy()
        else:
            if self.mode == "test":
                self.new_pos = [0, 0]
        
        for x in range(2):
            self.pos[x] += (self.new_pos[x] - self.pos[x])*.4
        
        self.norm = [self.pos[0] / self.extent, self.pos[1] / self.extent]
        self.rot = [self.norm[0]*cos(self.r) - self.norm[1]*sin(self.r),
                    self.norm[0]*sin(self.r) + self.norm[1]*cos(self.r)]
        actual_rotation = degrees(self.r + self.angle) % 360
        if self.text == None: 
            self.l.config(text=str([round(x, 2) for x in self.rot]))
            # self.l.config(text=str(self.root.server.gyro_angle))
        
        self.r += .01
        self.car_pos[0] += self.rot[0]
        self.car_pos[1] += self.rot[1]

        if self.mode == "test":
            v = rotate((self.car_pos[0], self.car_pos[1]-100), (self.car_pos[0], self.car_pos[1]), self.r)
            self.canvas.create_line(self.car_pos[0], self.car_pos[1], v[0], v[1], arrow="last", width=5, fill="blue")
            draw_rotated_rect(self.canvas, (self.car_pos[0], self.car_pos[1]), (80, 80), self.r, fill="yellow")
            self.canvas.create_line(self.car_pos[0], self.car_pos[1], self.rot[0]*200 + self.car_pos[0], self.rot[1]*200 + self.car_pos[1], arrow="last", width=5, fill="red")
    
    def loop(self):
        self.draw()
        self.root.after(16, self.loop)

    def press(self, event):
        self.m = [event.x, event.y]
        
    def release(self, event):
        self.m = None

win = Main()
win.mainloop()