#!/bin/bash

echo "Starting persistent Pyro4 nameserver ..."
if [ "$(pidof process_name)" ]
then
    echo "Nameserver already running ..."
else
    pyro4-ns -n 192.168.0.1 -s sql:ns.db &
fi

echo "Starting Control webserver ..."
python master.py
