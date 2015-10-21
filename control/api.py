import Pyro4
import bottle
import psutil
import json
import logging

apiApp = bottle.Bottle()
apiApp.log_client_mutex = None

@apiApp.route('/slaves')
def get_slaves():
    slave_data = []

    for name, slave in apiApp.slavemanager.slaves.items():
        try:
            status = slave.get_status()

            system_status = slave.get_system_status()
        except Pyro4.errors.CommunicationError as ex:
            status = "Communication error: '%s'" % (ex)
            system_status = {"load": 0, "mem_used": 0}

        slave_status = {
            "name": name,
            "address": slave._pyroUri.location,
            "status": status,
            "system_status": system_status,
        }

        slave_data.append(slave_status)

    return json.dumps(slave_data)


@apiApp.route('/status')
def get_status():
    traffic_total = apiApp.slavemanager.get_traffic_total()
    traffic_speed = apiApp.slavemanager.get_traffic_speed()

    return {
        "status": apiApp.slavemanager.status,
        "message": apiApp.slavemanager.status_message,
        "num_slaves": len(apiApp.slavemanager.slaves),
        "load": psutil.cpu_percent(),
        "traffic_total": (traffic_total[0], traffic_total[1]),
        "traffic_speed": (traffic_speed[0], traffic_speed[1]),
    }

@apiApp.post('/start-stream')
def start_stream():
    url = bottle.request.json['url']
    slave_name = bottle.request.json['slave']

    if not url:
        return { 'message': 'Empty URL!' }

    if slave_name == '*':
        slaves = apiApp.slavemanager.get_all_slaves()
    else:
        slaves = [apiApp.slavemanager.get_slave_by_name(slave_name),]

    for slave in slaves:
        try:
            logging.info("Starting stream %s on slave %s" % (url, slave))
            slave.start_stream(url)
        except Pyro4.errors.CommunicationError as ex:
            continue

    return { 'message': 'Starting stream!' }

@apiApp.post('/stop-stream')
def stop_stream():
    slave_name = bottle.request.json['slave']

    if slave_name == '*':
        slaves = apiApp.slavemanager.get_all_slaves()
    else:
        slaves = [apiApp.slavemanager.get_slave_by_name(slave_name),]

    for slave in slaves:
        try:
            logging.info("Stopping streams on slave %s" % (slave.name))
            slave.stop_stream()
        except Pyro4.errors.CommunicationError as ex:
            continue

    return { 'message': 'Stopping streams!' }

@apiApp.post('/display-image')
def display_image():
    url = bottle.request.json['url']
    slave_name = bottle.request.json['slave']

    if slave_name == '*':
        slaves = apiApp.slavemanager.get_all_slaves()
    else:
        slaves = [apiApp.slavemanager.get_slave_by_name(slave_name),]

    for slave in slaves:
        slave.display_image(url)

    return { 'message': 'Displaying image!' }

@apiApp.post('/hide-image')
def hide_image():
    slave_name = bottle.request.json['slave']

    if slave_name == '*':
        slaves = apiApp.slavemanager.get_all_slaves()
    else:
        slaves = [apiApp.slavemanager.get_slave_by_name(slave_name),]

    for slave in slaves:
        slave.hide_image()

    return { 'message': 'Hiding image!' }
