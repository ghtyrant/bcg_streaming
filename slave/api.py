import Pyro4
import bottle
import json
import psutil

apiApp = bottle.Bottle()


@apiApp.route('/slaves')
def slaves():
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
def status():
    traffic = psutil.network_io_counters()

    return {
        "status": apiApp.slavemanager.status,
        "message": apiApp.slavemanager.status_message,
        "num_slaves": len(apiApp.slavemanager.slaves),
        "load": psutil.cpu_percent(),
        "traffic": (traffic.bytes_sent, traffic.bytes_recv),
    }

@apiApp.post('/start-stream')
def start_stream():
    url = bottle.request.json['url']

    for _, slave in apiApp.slavemanager.slaves.items():
        slave.start_stream(url)

    return { 'message': 'Starting stream!' }

@apiApp.post('/stop-stream')
def stop_stream():
    for _, slave in apiApp.slavemanager.slaves.items():
        slave.stop_stream()

    return { 'message': 'Stoping streams!' }
