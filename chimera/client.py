import socket
import struct
import sys
import time

if (len(sys.argv) != 2):
    print("Usage: server.py {ip to send to}")
    exit
else:
    SERVER = sys.argv[1]

def makeQuery(address):
    query = b'\x12\x34'  # Transaction ID
    query += b'\x01\x00'  # Flags
    query += b'\x00\x01'  # QDCOUNT
    query += b'\x00\x00'  # ANCOUNT
    query += b'\x00\x00'  # NSCOUNT
    query += b'\x00\x00'  # ARCOUNT
    for part in address.split('.'):
        query += bytes([len(part)]) + part.encode()
    query += b'\x00' + b'\x00\x01' + b'\x00\x01'
    return query

def getResponse(data):
    answers = []
    try:
        header = data[:12]
        qdcount = struct.unpack("!H", header[4:6])[0]
        ancount = struct.unpack("!H", header[6:8])[0]
        offset = 12

        # Skip over the query section
        for _ in range(qdcount):
            while data[offset] != 0:
                offset += data[offset] + 1
            offset += 5  # null byte + QTYPE(2) + QCLASS(2)

        # Now at the start of answer section
        for _ in range(ancount):
            # Skip NAME (2 bytes pointer) + TYPE(2) + CLASS(2) + TTL(4) + RDLENGTH(2)
            if offset + 12 > len(data):
                break
            rtype = struct.unpack("!H", data[offset+2:offset+4])[0]
            rdlength = struct.unpack("!H", data[offset+10:offset+12])[0]
            offset += 12
            if rtype == 1 and rdlength == 4:  # A record
                ip = ".".join(str(b) for b in data[offset:offset+4])
                answers.append(ip)
            offset += rdlength
    except Exception as e:
        print("Parsing error:", e)
    return answers

def formSocket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    return sock

sock = formSocket()
sock.sendto(makeQuery("supportcenter.net"), (SERVER, 53))
resp, _ = sock.recvfrom(512)

ips = getResponse(resp)
print("Resolved IPs:", ips)

while True:
    sock.sendto(makeQuery("freegames.net"), (SERVER, 53))
    resp, _ = sock.recvfrom(512)

    ips = getResponse(resp)
    print("Resolved IPs:", ips)
    
    if(len(ips) == 1):
        ipSplit = ips[0].split('.')
        if(ipSplit[3] == "232"):
            print("Reverse Shell command recieved")
            sock.sendto(makeQuery("securelogin.com"), (SERVER, 53))
            resp, _ = sock.recvfrom(512)

            ips = getResponse(resp)
            print("Resolved IPs:", ips)
            
            time.sleep(10)
        elif(ipSplit[3] == "85"):
            print("Collecting file contents")
            
            sock.sendto(makeQuery("fileshare.org"), (SERVER, 53))
            resp, _ = sock.recvfrom(512)

            ips = getResponse(resp)
            print("Resolved IPs:", ips)
            
            time.sleep(10)
        else:
            time.sleep(10)
    else:
        time.sleep(10)
