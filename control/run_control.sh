#!/bin/bash

echo "Starting persistent Pyro4 nameserver ..."
pyro4-ns -s sql:ns.db &

echo "Starting Control webserver ..."
python master.py
