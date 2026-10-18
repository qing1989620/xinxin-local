#!/bin/sh
set -eu

# Alibaba's DNS, package mirrors and instance metadata use CGNAT addresses.
# Keep Tailscale's protection for new connections; allow established replies
# from these provider services on the existing default network interface.
device=$(ip -o -4 route show default | awk '{for (i=1;i<NF;i++) if ($i=="dev") {print $(i+1); exit}}')
case "$device" in
    ''|*[!a-zA-Z0-9_.:-]*) echo 'Cannot identify the cloud network interface' >&2; exit 1 ;;
esac

ready=0
for attempt in $(seq 1 30); do
    if iptables -w 3 -n -L ts-input >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 0.2
done
if [ "$ready" != 1 ]; then
    echo 'Tailscale input chain is not active; apply this helper again after joining the network' >&2
    exit 0
fi

for source in 100.100.2.0/24 100.100.100.200/32; do
    if ! iptables -w 3 -C ts-input -i "$device" -s "$source" \
        -m conntrack --ctstate ESTABLISHED,RELATED \
        -m comment --comment xinxin-aliyun-replies -j ACCEPT 2>/dev/null; then
        iptables -w 3 -I ts-input 1 -i "$device" -s "$source" \
            -m conntrack --ctstate ESTABLISHED,RELATED \
            -m comment --comment xinxin-aliyun-replies -j ACCEPT
    fi
done
