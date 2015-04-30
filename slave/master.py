import Pyro4
import bottle
import functools
import json

# Change SimpleTemplate syntax to AngularJS happy
MyAdapter = functools.partial(bottle.SimpleTemplate, syntax='<% %> % [[ ]]')
template = functools.partial(bottle.template, template_adapter=MyAdapter)


STATIC_VIEWS_DIR = "views"
STATIC_LIBS_DIR = "js"
STATIC_STYLES_DIR = "css"

SLAVES = {}

def fetch_slaves(ns):
    pass

@bottle.route("/")
def index():
    return bottle.static_file('index.html', root=STATIC_VIEWS_DIR)


@bottle.route('/js/<filepath:path>')
def staticJSGet(filepath):
    return bottle.static_file(filepath, root=STATIC_LIBS_DIR)


@bottle.route('/css/<filepath:path>')
def staticCSSGet(filepath):
    return bottle.static_file(filepath, root=STATIC_STYLES_DIR)


@bottle.route('/json/slaves')
def slaves():
    slave_data = []

    for slave, proxy in SLAVES.items():
        slave_data.append({"name": slave, "status": proxy.get_info()})

    return json.dumps(slave_data)

if __name__ == "__main__":
    ns = Pyro4.locateNS()
    slaves_addresses = ns.list(prefix="slave")

    print(slaves_addresses)

    print("Opening connection to slaves ...")
    SLAVES = {name: Pyro4.Proxy(address) for name, address in slaves_addresses.items()}

    for _, slave in SLAVES.items():
        print(slave.get_info())

    bottle.run(host="localhost", port=8080)
