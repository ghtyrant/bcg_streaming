import Pyro4
import bottle
import functools
import logging
import socket
import json
import threading
from loghandler import LogDispatchHandler, LogDispatchSubscriber

from api import apiApp
from slavemanager import SlaveManager

# Change SimpleTemplate syntax to AngularJS happy
MyAdapter = functools.partial(bottle.SimpleTemplate, syntax='<% %> % [[ ]]')
template = functools.partial(bottle.template, template_adapter=MyAdapter)


STATIC_VIEWS_DIR = "views"
STATIC_LIBS_DIR = "js"
STATIC_STYLES_DIR = "css"
STATIC_SCREENS_DIR = "screens"

app = bottle.Bottle()


# Index
@app.route("/")
def index():
    return bottle.static_file('index.html', root=STATIC_VIEWS_DIR)


# Static files (JS/CSS)
@app.route('/js/<filepath:path>')
def staticJSGet(filepath):
    return bottle.static_file(filepath, root=STATIC_LIBS_DIR)


@app.route('/css/<filepath:path>')
def staticCSSGet(filepath):
    return bottle.static_file(filepath, root=STATIC_STYLES_DIR)


@app.route('/screens/<slave_name>')
def staticScreenGet(slave_name):
    return bottle.static_file("%s.jpg" % (slave_name), root=STATIC_SCREENS_DIR)


class LogDispatchClient:
    def __init__(self, ws, loghandler):
        self.ws = ws
        self.loghandler = loghandler

    def run(self):
        sub = LogDispatchSubscriber()
        self.loghandler.subscribe(sub)

        while True:
            messages = sub.wait()

            if messages is not None:
                for msg in messages:
                    self.ws.send(json.dumps({"event": "log", "data": msg}))

            else:
                break

        self.loghander.unsubscribe(sub)


@app.route('/log')
def log():
    ws = bottle.request.environ.get('wsgi.websocket')
    if not ws:
        bottle.abort(400, 'Expected WebSocket request.')

    client = LogDispatchClient(ws, apiApp.loghandler)
    client.run()

if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer
    from geventwebsocket.handler import WebSocketHandler
    from gevent import monkey; monkey.patch_all()

    logger = logging.getLogger()

    handler = LogDispatchHandler()
    handler.setFormatter(logging.Formatter(fmt="[%(levelname)s] %(message)s"))

    logger.addHandler(handler)
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(logging.Formatter(fmt="[%(asctime)s][%(levelname)s] %(name)s :: %(message)s"))
    logger.addHandler(streamhandler)

    logger.setLevel(logging.DEBUG)

    logging.getLogger("geventwebsocket.handler").setLevel(logging.WARN)


    slavemanager = SlaveManager()

    bottle.debug(True)
    apiApp.slavemanager = slavemanager
    apiApp.loghandler = handler
    app.mount("/api/", apiApp)


    host = "127.0.0.1"
    port = 8080

    server = WSGIServer((host, port), app,
                        handler_class=WebSocketHandler)
    print "access @ http://%s:%s/websocket.html" % (host,port)

    try:
        server.serve_forever()
    except socket.error:
        logger.exception("Error starting bottle server:")

    print("Stopping slavemanager ...")
    slavemanager.stop()
