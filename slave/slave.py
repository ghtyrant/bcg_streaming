import sys
import Pyro4


class StreamSlaveControl:
    def __init__(self):
        self.testing = "Parameter"

    def get_info(self):
        return "This is just a test!"


def generate_free_name(ns):
    registered_slaves = ns.list(prefix="slave")

    max_num = 0
    for slave, _ in registered_slaves.items():
        num = int(slave.split(".")[1])

        if num > max_num:
            max_num = num

    max_num += 1

    return "slave.%d" % (max_num)


if __name__ == "__main__":
    daemon = Pyro4.Daemon()
    print("Locating nameserver ...")
    ns = Pyro4.locateNS()
    uri = daemon.register(StreamSlaveControl())

    if len(sys.argv) == 2:
        name = "slave.%s" % (sys.argv[1])
    else:
        name = generate_free_name(ns)

    print("Registering with nameserver (name: %s) ..." % (name))
    ns.register(name, uri, safe=True)

    print("Done! Starting event loop ...")
    daemon.requestLoop()

    print("Removing ourself from the name server ...")
    ns.remove(name)
    print("Good bye!")
