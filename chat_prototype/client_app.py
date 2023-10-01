import socket
import pickle
import time


HEADERSIZE = 10

# streaming socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostname(),60001))


while True:

    full_msg = b''
    new_msg = True

    while True:
        msg = s.recv(1024)
        if new_msg:
            print(f'new message length: {msg[:HEADERSIZE]}')
            msglen = int(msg[:HEADERSIZE])
            new_msg = False

        full_msg += msg.decode("utf-8")
        #print(msg.decode("utf-8"))

        if(len(full_msg)-HEADERSIZE) == msglen:
            print("full msg received")
            print(full_msg[HEADERSIZE:])

            d = pickle.loads(full_msg[HEADERSIZE:])
            print(d)

            new_msg = True
            full_msg = b''
        print(full_msg)