import socket, time, json, threading, sys
from customtkinter import *
from tkinter import messagebox
from os.path import join, dirname

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = CTkLabel(master=self, justify=LEFT, text="addr: XXX.XXX.X.XX")
        label.pack(pady=10, padx=10)

        self.current_speed = 1
        self.active = False

        # Current Speed Frame
        self.current_speed_frame = CTkFrame(master=self)
        self.current_speed_frame.pack(pady=10, padx=10)

        self.current_speed_pb = CTkProgressBar(master=self.current_speed_frame)
        self.current_speed_pb.pack(pady=10, padx=10, side=LEFT)
        self.current_speed_pb.set(self.current_speed)
        
        self.current_speed_label = CTkLabel(master=self.current_speed_frame, text=str(self.current_speed))
        self.current_speed_label.pack(pady=10, padx=10, side=LEFT)

        self.set_speed_frame = CTkFrame(master=self)
        self.set_speed_frame.pack(pady=10, padx=10)

        # Set Speed Frame
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

    def slider_speed_callback(self, value):
        self.current_speed = value

    def toggle_state(self):
        self.active = not self.active
        self.switch.configure(text="Inactive Active".split()[int(self.active)])

set_appearance_mode("system")
set_default_color_theme("blue")

app = CTk()
app.geometry("1280x720")
app.title("Soccer Robots Controllor")

themes_label = CTkLabel(master=app, text="Theme")
themes_label.pack()
themes_option_menu = CTkOptionMenu(master=app, values=["blue", "dark-blue", "green"])
themes_option_menu.pack()

frame_1 = RobotFrame(master=app)
frame_1.pack(pady=20, padx=60, fill="both", expand=True, side=LEFT)

frame_2 = RobotFrame(master=app)
frame_2.pack(pady=20, padx=60, fill="both", expand=True, side=RIGHT)

data = json.load(open(join(dirname(__file__), "./options.json"), "r"))
server = Server(host_addr = data["host_address"], host_port=data["host_port"])

thread = threading.Thread(target=server.run)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        app.destroy()
        server.close()
        sys.exit()

app.protocol("WM_DELETE_WINDOW", on_closing)
app.after(50, thread.start)
app.mainloop()