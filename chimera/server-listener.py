import socket
import sys
import os

port = 10000

if (len(sys.argv) != 2):
    print("Usage: server-listener.py {ip to listen on}")
    exit
else:
    bind_ip = sys.argv[1]

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
        
        if (len(dataSplit) == 1):
            if (dataSplit[0] == "check"):
                sock.sendto("confirm".encode(), addr)
            elif (dataSplit[0] == "status"):
                response = []
                beaconFiles = os.listdir('/tmp/chimera')
                beaconFiles = [f for f in beaconFiles if os.path.isfile(os.path.join('/tmp/chimera', f))]
                
                for beacon in beaconFiles:
                    beaconEntry = [str(beacon)]
                    f = open("/tmp/chimera/" + beacon, "r")
                    cont = f.read()
                    contSplit = cont.split('\n')
                    line = contSplit[0]
                    lineSplit = line.split(': ')
                    time = lineSplit[1]
                    beaconEntry.append(time)
                    beaconEntry = '|'.join(beaconEntry)
                    response.append(beaconEntry)
                
                response = ';'.join(response)
                
                sock.sendto(response.encode(), addr)
            else:
                pass
        elif (len(dataSplit) == 2):
            if (dataSplit[0] == "status") and (len(dataSplit[1].split('.')) == 4):
                if not os.path.exists("/tmp/chimera/" + dataSplit[1]):
                    sock.sendto("not_found".encode(), addr)
                else:
                    response = []
                    f = open("/tmp/chimera/" + dataSplit[1], "r")
                    cont = f.read()
                    contSplit = cont.split('\n')
                    response.append((contSplit[0].split(': '))[1])
                    del(contSplit[0])
                    response = response + contSplit
                    sock.sendto(response.encode(), addr)
        else:
            pass
            
run()