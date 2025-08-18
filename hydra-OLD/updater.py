#!/usr/bin/env python3
import os
import time

def main():
    os.system("rm /bin/hydra")
    os.system("rm /lib/Hydra/version")
    os.system("mv /tmp/github/Hydra/version /lib/Hydra/version")
    os.system("mv /tmp/github/Hydra/main.py /bin/hydra")
    os.system("chmod +x /bin/hydra")
main()