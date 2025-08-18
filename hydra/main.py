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
          
main()