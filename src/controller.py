import socket, json, threading, sys
from time import sleep
from customtkinter import *
from tkinter import messagebox
from os.path import join, dirname
from math import atan2, cos, sin, sqrt, radians, pi

BLUETOOTH = 0xF0
LOCALHOST = 0xF1
CONNECTION_MODE = LOCALHOST

def read_options() -> dict:
    return json.load(open(join(dirname(__file__), "./options.json"), "r"))

def write_options(obj):
    data = read_options()
    try:
        json.dump(obj, open(join(dirname(__file__), "./options.json"), "w"), sort_keys=True, indent=4)
    except:
        json.dump(data, open(join(dirname(__file__), "./options.json"), "w"), sort_keys=True, indent=4)
        raise

class App(CTk):
    def __init__(self):
        super().__init__()

        win_size = (1280, 720)
        wx = (self.winfo_screenwidth() - win_size[0]) // 2
        wy = (self.winfo_screenheight() - win_size[1]) // 2

        self.geometry("%dx%d+%d+%d" % (win_size[0], win_size[1], wx, wy))
        self.minsize(win_size[0], win_size[1])
        self.maxsize(win_size[0], win_size[1])
        self.title("Soccer Robots Controllor")

        self.current_ui = []
        self.pending_labels = [
            CTkLabel(master=self, text="Waiting for connection..."),
            CTkLabel(master=self, text="Waiting for connection...")
        ]

        self.main_content = MainFrame(self, self.change_theme)
        self.current_ui.append(self.main_content)

        self.pending_labels[0].place(relwidth=0.5, relheight=1, relx=0, rely=0)
        self.pending_labels[1].place(relwidth=0.5, relheight=1, relx=0.5, rely=0)
        [pl.lift() for pl in self.pending_labels]

        self.server = Server(master=self, host_addr = data["host_address"], host_port = data["host_port"])

        self.thread = threading.Thread(target=self.server.run)

        self.after(50, self.thread.start)
        self.after(50, self.update)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update(self):
        if not self.server.active:
            sys.exit()

        # Joystick movement
        move_angle_1, move_speed_1 = self.main_content.frame_1.get_movement_value()
        move_angle_2, move_speed_2 = self.main_content.frame_2.get_movement_value()
        if move_angle_1 and move_speed_1: self.server.send(0, "move %s %s" % (str(move_angle_1), str(move_speed_1)))
        if move_angle_2 and move_speed_2: self.server.send(1, "move %s %s" % (str(move_angle_2), str(move_speed_2)))

        self.after(50, self.update)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            for client in self.server.clients:
                client.close()
            self.server.close()
            self.destroy()
            sys.exit()

    def reset_current_ui(self):
        for widget in self.current_ui:
            widget.destroy()
        self.main_content = MainFrame(self, self.change_theme)
        self.main_content.pack(expand=True, fill=BOTH)
        self.current_ui.append(self.main_content)

    def change_theme(self, theme_name):
        data = read_options()
        if theme_name != data["gui_theme"]:
            data["gui_theme"] = theme_name
            write_options(data)

            set_default_color_theme(theme_name.lower())
            self.reset_current_ui()
            self.main_content.themes_frame.place(relx=0, rely=1, anchor="sw")
            self.main_content.themes_frame.lift()

class Server:
    def __init__(self, master: App, host_addr, host_port):
        self.parent: App = master

        self.active = True

        self.size = 1024
        if CONNECTION_MODE == BLUETOOTH:
            self.addr = host_addr
            self.port = host_port
            self.server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        elif CONNECTION_MODE == LOCALHOST:
            self.addr = "127.0.0.1"
            self.port = 8080
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
        self.server.bind((self.addr, self.port))
        self.server.listen(1) # Only two connections allowed
        print("Server is listening on %s:%d" % (self.addr, self.port))
        
        self.clients = []

    def run(self):
        while len(self.parent.pending_labels) > 0:
            try:
                client, addr = self.server.accept()
                t = threading.Thread(target=self.on_new_client, args=(client, addr))
                t.start()
                if len(self.clients) == 2:
                    self.parent.main_content.themes_frame.place(relx=0, rely=1, anchor="sw")

            except OSError: return 0
            except: raise

            sleep(0.01)
    
    def on_new_client(self, client, addr):
        self.clients.append(client)
        
        if len(self.parent.pending_labels) == 2:
            self.parent.main_content.pack(expand=True, fill=BOTH)
        self.parent.pending_labels[0].destroy()
        self.parent.pending_labels.pop(0)

        print("Client connected " + str(addr))

        while True:
            try:
                request = client.recv(self.size)
                
                if request:
                    content = request.decode()
                    print(content)
                else:
                    break
            except ConnectionAbortedError: break
            except: raise

        print("Disconnected")
        self.close()
        self.active = False

    def close(self):
        self.server.close()

    def send(self, index, content):
        if index >= len(self.clients):
            return
        if isinstance(self.clients[index], socket.socket):
            self.clients[index].send(str(content).encode())
        else:
            raise Exception("Server.send(content): Client is not connected.")

class MainFrame(CTkFrame):
    def __init__(self, master: App, change_theme):
        super().__init__(master=master)

        self.parent: App = master

        data = read_options()

        self.frame_1 = RobotFrame(number=1, master=self)
        self.frame_1.pack(pady=80, padx=50, fill="both", expand=True, side=LEFT)

        self.frame_2 = RobotFrame(number=2, master=self)
        self.frame_2.pack(pady=80, padx=50, fill="both", expand=True, side=RIGHT)

        self.themes_frame = CTkFrame(master=self.parent)
        self.themes_label = CTkLabel(master=self.themes_frame, text="Theme")
        self.themes_label.pack()
        self.themes_option_menu = CTkOptionMenu(master=self.themes_frame, command=change_theme, values=["blue", "dark-blue", "green"])
        self.themes_option_menu.set(data["gui_theme"])
        self.themes_option_menu.pack()

class RobotFrame(CTkFrame):
    def __init__(self, master: MainFrame, number=None, *args, **kwargs):
        if not number:
            raise Exception("No number provided")

        super().__init__(master=master, *args, **kwargs)

        self.parent: MainFrame = master

        title = CTkLabel(master=self, justify=LEFT, text="addr: XXX.XXX.X.XX")
        title.pack(pady=10, padx=10)

        self.number = number

        data = read_options()
        robot_data = data["robot_{}".format(str(number))]

        self.current_speed = round(robot_data["speed"], 3)
        self.active = False

        # Current Speed Frame
        self.current_speed_frame = CTkFrame(master=self)
        self.current_speed_frame.pack(pady=10, padx=10)

        label = CTkLabel(master=self.current_speed_frame, justify=LEFT, text="Current Speed")
        label.pack()

        self.current_speed_pb = CTkProgressBar(master=self.current_speed_frame)
        self.current_speed_pb.pack(padx=10, side=LEFT)
        self.current_speed_pb.set(self.current_speed)
        
        self.current_speed_label = CTkLabel(master=self.current_speed_frame, text=str(self.current_speed))
        self.current_speed_label.pack(padx=10, side=LEFT)

        # Set Speed Frame
        self.set_speed_frame = CTkFrame(master=self)
        self.set_speed_frame.pack(pady=10, padx=10)

        self.set_speed_slider = CTkSlider(master=self.set_speed_frame, command=self.slider_speed_callback, from_=0, to=1)
        self.set_speed_slider.pack(pady=10, padx=10, side=LEFT)
        self.set_speed_slider.set(self.current_speed)

        self.set_speed_button = CTkButton(master=self.set_speed_frame, command=self.set_speed, text="Set speed")
        self.set_speed_button.pack(pady=10, padx=10, side=LEFT)

        # Toggle Robot On and Off 
        self.switch = CTkSwitch(master=self, command=self.toggle_state, text="Inactive")
        self.switch.pack(pady=10, padx=10)

        # Joysticks
        self.movement_joystick = Joystick(master=self, relpos=(0, 1),
                                                size=(501, 501), center=(250, 250),
                                                radius=170, cursor_radius=80, bg=rgb_to_hex((70, 70, 70)), anchor="sw")
        self.calibration_joystick = Joystick(master=self, relpos=(.67, 1),
                                                size=(261, 261), center=(130, 130),
                                                radius=85, cursor_radius=45, bg=rgb_to_hex((55, 55, 55)), anchor="sw",
                                                mode="stiff", text="Calibration")
        self.movement_joystick.loop()
        self.calibration_joystick.loop()
        try:
            self.calibration_joystick.angle = radians(self.server.gyro_angle)
        except: pass

    def set_speed(self):
        self.current_speed_pb.set(self.current_speed)
        self.current_speed_label.configure(text=str(self.current_speed))
        
        data = read_options()
        data["robot_{}".format(str(self.number))]["speed"] = self.current_speed
        write_options(data)

        self.parent.parent.server.send(
            index=self.number-1,
            content=f"set_speed {str(self.current_speed)}"
        )

    def slider_speed_callback(self, value):
        self.current_speed = round(value, 2)

    def toggle_state(self):
        self.active = not self.active
        self.switch.configure(text="Inactive Active".split()[int(self.active)])

        self.parent.parent.server.send(
            index=self.number-1,
            content=f"set_state {str(int(self.active))}"
        )

    def get_movement_value(self):
        if self.movement_joystick.pressed:
            angle = round((atan2(self.movement_joystick.norm[1], self.movement_joystick.norm[0]) + self.calibration_joystick.angle + pi/2) % (2*pi), 3)
            speed = round(self.movement_joystick.dist, 3)
            return angle, speed
        else:
            return None, None
        
def rgb_to_hex(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code"""
    return "#%02x%02x%02x" % rgb   

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
    def __init__(self, master, relpos, size, center, radius, cursor_radius, fill="grey", cursor_colour="darkgrey", bg="white", mode="normal", text=None, anchor="n"):
        self.master = master
        self.mode = mode

        self.pos = [0, 0]
        self.new_pos = self.pos.copy()

        self.pressed = None

        self.angle = 0
        self.norm = [0, 0]
        self.dist = 0

        self.center = center
        self.extent = radius
        self.cursor_rad = cursor_radius
        self.fill = fill
        self.cursor_colour = cursor_colour

        self.text = text

        colour = ThemeManager.theme['CTkFrame']["top_fg_color"][1][-2:]
        if colour == "00": colour = "100"
        colour = round(int(colour) * 2.55)
        colour = rgb_to_hex((colour, colour, colour))

        self.cw = size[0]
        self.ch = size[1]
        self.canvas = CTkCanvas(master, width=self.cw, height=self.ch, bg=colour, bd=0, relief='ridge', highlightthickness=0)
        self.canvas.place(relx=relpos[0], rely=relpos[1], anchor=anchor, bordermode="inside")

        self.canvas.bind('<B1-Motion>', self.press)
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<ButtonRelease-1>', self.release)

    def draw(self):
        self.canvas.delete('all')
        self.canvas.create_aa_circle(x_pos=self.center[0], y_pos=self.center[1], radius=self.extent, angle=0, fill=self.cursor_colour)
        self.canvas.create_aa_circle(x_pos=self.center[0], y_pos=self.center[1], radius=self.extent - 2, angle=0, fill=self.fill)
        self.canvas.create_aa_circle(x_pos=self.center[0] + self.pos[0], y_pos=self.center[1] + self.pos[1], radius=self.cursor_rad, angle=0, fill=rgb_to_hex((0, 0, 0)))
        self.canvas.create_aa_circle(x_pos=self.center[0] + self.pos[0], y_pos=self.center[1] + self.pos[1], radius=self.cursor_rad - 2, angle=0, fill=self.cursor_colour)
        
        if self.pressed:
            t = [self.pressed[0] - self.center[0], self.pressed[1] - self.center[1]]
            if not(t[0]*t[0] + t[1]*t[1] < self.extent**2) or self.mode == "stiff":
                a = atan2(t[1], t[0])
                self.angle = a
                self.new_pos = [self.extent*cos(a), self.extent*sin(a)]
            else:
                self.new_pos = t.copy()
        else:
            if self.mode == "normal":
                self.new_pos = [0, 0]
        
        self.pos[0] += (self.new_pos[0] - self.pos[0])*.5
        self.pos[1] += (self.new_pos[1] - self.pos[1])*.5
        
        self.norm = [self.pos[0] / self.extent, self.pos[1] / self.extent]
        self.dist = sqrt(self.norm[0]**2 + self.norm[1]**2)
        
    def loop(self):
        self.draw()
        self.master.after(15, self.loop)

    def press(self, event):
        self.pressed = [event.x, event.y]
        
    def release(self, event):
        self.pressed = None

if __name__ == "__main__":
    data = read_options()

    set_appearance_mode("dark")
    set_default_color_theme(data["gui_theme"])

    app = App()
    app.mainloop()