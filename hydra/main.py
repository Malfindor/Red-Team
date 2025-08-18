#!/usr/env/python3
import file
import paramiko
import os
import sys
import random

def main():
    os.system("rm -rf /tmp/github")
    print("Checking for updates...")
    if(updatePend()):
        option = input ("An update is available. Would you like to update? ")
        if(option.lower() == "y" or option.lower() == "yes"):
            os.system("python3 /lib/Hydra/updater.py &")
            return
    else:
        print("Hydra is up to date.")
     
def getIP(machine):
    return {
            'docker': '172.25.x.97',
            'debian': '172.25.x.20',
            'ubuntu': '172.25.x.23',
            'WinAD': '172.25.x.27',
            'splunk': '172.25.x.9',
            'ecom': '172.25.x.11',
            'fedora': '172.25.x.39'
        }.get(machine, "")

    
main()