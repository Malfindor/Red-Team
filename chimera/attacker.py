import socket
import sys

def runInteractive(SERVER):
    if (SERVER == ""):
        x = True
        while x:
            enteredAddress = input("Enter server address: ")
            if (len(enteredAddress.split('.')) == 4):
                x = False
                SERVER = enteredAddress
            else:
                print("Invalid address entered. Please enter the IPv4 address of the Chimera server.")
    if not checkConn():
        print(f"Unable to reach server at {SERVER}, connection failure or timeout.")
        connected = False
    else:
        print(f"Successfully reached Chimera server at {SERVER}")
        connected = True
    
    if not connected:
        return
    
    z = True
    
    while z:
        command = input("Enter command: ")
        if (command == "exit"):
            z = False
        elif (command == "list"):
            timeout = False
            sock.sendto("status".encode(),(SERVER, 10000))
            try:
                resp, _ = sock.recvfrom(512)
            except socket.timeout:
                print("Socket timeout. Server may be down or otherwise unresponsive.")
                timeout = True
            if not timeout:
                response = resp.decode()
                beaconList = response.split(';')
                print("Beacon IP ||| Last Heard From")
                print("----------------------------------")
                for beacon in beaconList:
                    beacon = beacon.split('|')
                    print(beacon[0] + " -- " + beacon[1])
                print("")
        else:
            printCommHelp()

def runStandard():
    pass

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
        
def printHelp():
    print("""
    
    
    
    
    
    
""")

def printCommHelp():
    print("""
    Chimera server commands
---------------------------------

exit - exits out of the client
list - collects a list of all beacons registered to the server, along with their last-heard-from date/time
    
    
""")
    
sock = formSocket()
if (len(sys.argv) == 1):
    runInteractive("")
elif (len(sys.argv) == 2):
    if not (len(sys.argv[1].split('.')) == 4):
        print("Invalid IP address. Note: This will only accept IPv4 addresses.")
    else:
        SERVER = sys.argv[1]
        runInteractive(SERVER)
else:
    printHelp()
