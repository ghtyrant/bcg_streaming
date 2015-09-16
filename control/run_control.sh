#!/bin/bash

echo "Starting Pyro4 nameserver ..."
pyro4-ns&

echo "Starting Control webserver ..."
python master.py
