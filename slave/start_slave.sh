#!/bin/sh

function get_ip() {
	local IP_ADDR=$(ip addr show eth0 | grep 192.168 | tail -1 | cut -d' ' -f 6 | cut -d'/' -f 1)
	echo $IP_ADDR
}

IP=$(get_ip)
echo "IP: $IP"
python2 /home/alarm/bcg_streaming/slave/slave.py $IP
