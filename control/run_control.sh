#!/bin/bash

IP="192.168.1.121"

echo "Starting persistent Pyro4 nameserver ..."
pyro4-ns -n $IP &
PID=$!

echo "Starting Control webserver ..."
python master.py $IP

trap "kill $PID; exit 1" INT
