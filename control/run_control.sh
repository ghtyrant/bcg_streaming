#!/bin/bash

echo "Starting persistent Pyro4 nameserver ..."
pyro4-ns -n 0.0.0.0 -s sql:ns.db &

echo "Starting Control webserver ..."
python master.py

kill $!
