import socket
import sys

def run(HOST, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        print("Recieved connection from " + addr[0])
        with conn:
            while True:
                cmd = input(str(addr[0]) + "# ")
                if cmd.lower() == "exit":
                    print("Closing...")
                    break
                conn.send(cmd.encode())
                data = conn.recv(4096)
                print(data.decode(), end="")

if not (len(sys.argv) == 3):
    print("Usage: shellServer.py {ip to listen on} {port to listen on}")
elif not ((len(sys.argv[1].split('.')) == 4) and (int(sys.argv[2]) > 0 and int(sys.argv[2]) <= 510)):
    print("Invalid IP or port. Note: port range is between 1-510")
else:
    run(sys.argv[1], int(sys.argv[2]))