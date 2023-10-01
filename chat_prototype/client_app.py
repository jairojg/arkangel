import socket
import pickle
import time
from PIL import Image

# Data
IMG_PATH = "./data/test_img/ai.jpg"

# Networking parameters
HEADERSIZE = 10
PORT = 1240
IP = '127.0.0.1'

# run sockets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

# load and send image
image = Image.open(IMG_PATH)
msg = pickle.dumps(image)
client_socket.send(msg)


"""
in_msg = b""
while True:
    packet = client_socket.recv(4096)
    if not packet: break
    in_msg += packet


print(in_msg.decode("utf-8"))
print("-----------")
"""