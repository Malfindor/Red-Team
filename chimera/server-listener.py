import socket
import sys
import os

bind_ip = "127.0.0.1"
port = 10000

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, port))
    print(f"[+] Chimera command server listening on {bind_ip}:{port}")
    
    if not os.path.exists("/tmp/chimera/"):
        os.system("mkdir /tmp/chimera/")
    
    while True:
        data, addr = sock.recvfrom(512)
        print(f"Recieved command from {addr[0]}:{addr[1]}")
        
        dataSplit = data.decode().split(":")
        
        if (dataSplit[0] == "check"):
            sock.sendto("confirm".encode(), addr)
        elif (dataSplit[0] == "status"):
            pass
        else:
            pass
            
run()