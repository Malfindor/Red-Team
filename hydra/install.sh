#!/bin/bash
if ! [ $UID == 0 ]
then
echo "Must be run as root."
fi
if [ $UID == 0 ]
then
apt-get update && apt-get install -y python3 
apt-get update && apt-get install -y pip
pip install paramiko
pip install file
repo_root=$(git rev-parse --show-toplevel)
mv $repo_root/Hydra/main.py /bin/hydra
mkdir /lib/Hydra
touch /lib/Hydra/network.conf
touch /lib/Hydra/record.stor
mv $repo_root/Hydra/legend.list /lib/Hydra/legend.list
mv $repo_root/Hydra/updater.py /lib/Hydra/updater.py
mv /$repo_root/Hydra/version /lib/Hydra/version
chmod +x /bin/hydra
rm $0
fi