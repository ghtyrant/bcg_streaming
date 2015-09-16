import Pyro4
import bottle
import functools
import logging
import socket

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


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG)
    logger = logging.getLogger("")

    slavemanager = SlaveManager()

    bottle.debug(True)
    apiApp.slavemanager = slavemanager
    app.mount("/api/", apiApp)
    try:
        app.run(host="localhost", port=8080, reloader=False)
    except socket.error:
        logger.exception("Error starting bottle server:")

    print("Stopping slavemanager ...")
    slavemanager.stop()
