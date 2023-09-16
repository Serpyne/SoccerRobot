import socket, time, json, threading, sys
from customtkinter import *
from tkinter import messagebox
from os.path import join, dirname

def read_options() -> dict:
    return json.load(open(join(dirname(__file__), "./options.json"), "r"))

class Server:
    def __init__(self, host_addr, host_port):
        self.addr = host_addr
        self.port = host_port
        self.backlog = 1
        self.size = 1024

        self.server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.server.bind((self.addr, self.port))
        self.server.listen(self.backlog)
        print("Server is listening on %s:%d" % (self.addr, self.port))

        self.client = None

    def run(self):
        try:
            self.client, addr = self.server.accept()
        except OSError: return 0
        except: raise
        
        print("Client connected " + str(addr))

        self.client.send("PING".encode())

        request = self.client.recv(self.size)
        if request.decode() == "PONG":
            print("Connection established")
        else:
            self.close()

        while True:
            request = self.client.recv(self.size)
            
            if request:
                content = request.decode()

                print(content)

            else:
                break

        print("Disconnected")
        self.close()

    def close(self):
        if self.client:
            self.client.close()
        self.server.close()

    def send(self, content):
        if isinstance(self.client, socket.socket):
            self.client.send(content.encode())
        else:
            raise Exception("Error in Server.send(content): Client is not connected.")

class RobotFrame(CTkFrame):
    def __init__(self, number=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not number:
            raise Exception("No number provided")

        title = CTkLabel(master=self, justify=LEFT, text="addr: XXX.XXX.X.XX")
        title.pack(pady=10, padx=10)

        self.number = number

        data = read_options()
        robot_data = data["robot_{}".format(str(number))]

        self.current_speed = robot_data["speed"]
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

        self.switch = CTkSwitch(master=self, command=self.toggle_state, text="Inactive")
        self.switch.pack(pady=10, padx=10)

    def set_speed(self):
        self.current_speed_pb.set(self.current_speed)
        self.current_speed_label.configure(text=str(self.current_speed))
        
        data = read_options()
        data["robot_{}".format(str(self.number))]["speed"] = self.current_speed
        with open(join(dirname(__file__), "./options.json"), "w") as f:
            json.dump(data, f)

    def slider_speed_callback(self, value):
        self.current_speed = value

    def toggle_state(self):
        self.active = not self.active
        self.switch.configure(text="Inactive Active".split()[int(self.active)])

class MainFrame(CTkFrame):
    def __init__(self, app, change_theme):
        super().__init__(master=app)

        data = read_options()

        self.themes_label = CTkLabel(master=self, text="Theme")
        self.themes_label.pack()
        self.themes_option_menu = CTkOptionMenu(master=self, command=change_theme, values=["blue", "dark-blue", "green"])
        self.themes_option_menu.set(data["gui_theme"])
        self.themes_option_menu.pack()

        self.frame_1 = RobotFrame(number=1, master=self)
        self.frame_1.pack(pady=20, padx=60, fill="both", expand=True, side=LEFT)

        self.frame_2 = RobotFrame(number=2, master=self)
        self.frame_2.pack(pady=20, padx=60, fill="both", expand=True, side=RIGHT)

class App(CTk):
    def __init__(self):
        super().__init__()

        self.geometry("1280x720")
        self.title("Soccer Robots Controllor")

        self.current_ui = []

        self.main_content = MainFrame(self, self.change_theme)
        self.main_content.pack(expand=True, fill=BOTH)
        self.current_ui.append(self.main_content)

        self.server = Server(host_addr = data["host_address"], host_port=data["host_port"])

        self.thread = threading.Thread(target=self.server.run)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(50, self.thread.start)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            app.destroy()
            self.server.close()
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
            json.dump(data, open(join(dirname(__file__), "./options.json"), "w"), sort_keys=True, indent=4)

            set_default_color_theme(theme_name.lower())
            self.reset_current_ui()

if __name__ == "__main__":
    data = read_options()

    set_appearance_mode("dark")
    set_default_color_theme(data["gui_theme"])

    app = App()
    app.mainloop()