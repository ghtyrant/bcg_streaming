#!/bin/bash

echo "Starting persistent Pyro4 nameserver ..."
if [ "$(pidof process_name)" ]
then
    echo "Nameserver already running ..."
else
    pyro4-ns -n 0.0.0.0 -s sql:ns.db &
fi

echo "Starting Control webserver ..."
python master.py
