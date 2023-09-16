import socket, json, threading, sys
from time import sleep
from customtkinter import *
from tkinter import messagebox
from os.path import join, dirname

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

        self.geometry("1280x720")
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

        self.addr = "127.0.0.1"
        self.port = 8080
        # self.addr = host_addr
        # self.port = host_port
        self.size = 1024

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
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
            self.clients[index].send(content.encode())
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
        write_options(data)

        self.parent.parent.server.send(
            index=self.number-1,
            content=f"set_speed {str(self.current_speed)}"
        )

    def slider_speed_callback(self, value):
        self.current_speed = value

    def toggle_state(self):
        self.active = not self.active
        self.switch.configure(text="Inactive Active".split()[int(self.active)])

        self.parent.parent.server.send(
            index=self.number-1,
            content=f"set_state {str(int(self.active))}"
        )

if __name__ == "__main__":
    data = read_options()

    set_appearance_mode("dark")
    set_default_color_theme(data["gui_theme"])

    app = App()
    app.mainloop()