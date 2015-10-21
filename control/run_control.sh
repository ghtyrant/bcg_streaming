#!/bin/bash

echo "Starting persistent Pyro4 nameserver ..."
pyro4-ns -n 192.168.0.1 &
PID=$!

echo "Starting Control webserver ..."
python master.py

trap "kill $PID; exit 1" INT
