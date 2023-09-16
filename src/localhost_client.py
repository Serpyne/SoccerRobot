#!/usr/bin/env python3

import threading, json, socket
from time import sleep
from os.path import join, dirname
from math import pi, cos, sin, atan2, radians, sqrt

data = json.load(open(join(dirname(__file__), "./options.json")))
target_host = data["host_address"]
target_port = data["host_port"]

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
client.settimeout(1)

# client.connect((target_host, target_port))
client.connect(('127.0.0.1', 8080))
print("Connected on " + str(client.getsockname()))

def request_handler():
    while True:
        try:
            request = client.recv(1024)
            if request:
                print(request.decode())
        except TimeoutError: pass
        except ConnectionResetError: break
        except: raise

        sleep(0.01)

    print("Disconnected from server, closing client..")
    client.close()

request_handler()
