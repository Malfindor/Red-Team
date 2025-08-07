import socket
import sys

def runInteractive():
    pass

def runStandard():
    if not checkConn():
        print(f"Unable to reach server at {SERVER}, connection failure or timeout.")
    else:
        print(f"Successfully reached Chimera server at {SERVER}")

def formSocket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    return sock

def checkConn():
    sock.sendto("check".encode(),(SERVER, 10000))
    try:
        resp, _ = sock.recvfrom(512)
    except socket.timeout:
        return False
    if (resp.decode() == "confirm"):
        return True
    else:
        return False
    
sock = formSocket()
if (len(sys.argv) == 1):
    runInteractive()
elif (len(sys.argv) == 2):
    if not (len(sys.argv[1].split('.')) == 4):
        print("Invalid IP address. Note: This will only accept IPv4 addresses.")
    else:
        SERVER = sys.argv[1]
        runStandard()
else:
    print("Run with no arguments for interactive, otherwise run like: attacker.py {server address}")
