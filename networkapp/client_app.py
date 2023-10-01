import socket
import pickle
import argparse
from PIL import Image
import select
from time import sleep

parser = argparse.ArgumentParser()
parser.add_argument("-p","--port", type=int, help="TCP/IP port",
                    required=True)
parser.add_argument("-i","--ip_direction", type=str, help="ip direction",
                    required=True)
parser.add_argument("-f","--img_path", type=str, help='image to analyze',
                    required=True)

args = parser.parse_args()
cli_arguments = vars(args)

# Data
IMG_PATH = cli_arguments['img_path']

# Networking parameters
PORT = cli_arguments['port']
IP = cli_arguments['ip_direction']

# run sockets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
#client_socket.settimeout(10)
#client_socket.setblocking(False)

print(f"connection stablished at {IP}:{PORT}")
    
# load and send image
image = Image.open(IMG_PATH)
msg_out = pickle.dumps(image)
client_socket.send(msg_out)
print("image sent to {IP}:{PORT}")
client_socket.close()
print("closing")
