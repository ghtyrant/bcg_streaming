import bottle
import json

apiApp = bottle.Bottle()


@apiApp.route('/slaves')
def slaves():
    slave_data = []

    for name, slave in apiApp.slavemanager.slaves.items():
        slave_data.append({"name": name, "status": slave.get_info()})

    return json.dumps(slave_data)
