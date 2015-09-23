#!/bin/bash

echo "Starting persistent Pyro4 nameserver ..."
pyro4-ns -d&

echo "Starting Control webserver ..."
python master.py
