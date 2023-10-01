import socket
import time
import pickle






HEADERSIZE = 10
msg = "welcome"
print(f'{len(msg):<10}'+msg)

# streaming socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(),60001))
s.listen(5)

while(True):
    clientsocket, address = s.accept()
    print(f"connection establised from  {address} has been stablised")
    
    tmp_d = {'a':1,'b':2}
    msg = pickle.dumps(tmp_d)
    print(msg)
    
    msg = bytes(f'{len(msg):<{HEADERSIZE}}',"utf-8")+msg
    
    clientsocket.send(bytes(msg,"utf-8"))

