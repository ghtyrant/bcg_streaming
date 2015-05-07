import Pyro4
import threading
import time
import logging


class SlaveManager:
    STATUS_OFFLINE = 0
    STATUS_ONLINE = 1
    def __init__(self):
        self.nameserver = Pyro4.locateNS()
        self.slaves = {}

        self.set_status(SlaveManager.STATUS_OFFLINE, "Starting up ...")

        self.stopped = False

        self.update_thread = threading.Thread(target=self.thread_update_slaves)
        self.update_thread.start()

    def thread_update_slaves(self):
        while not self.stopped:
            self.update_slaves()
            time.sleep(5)

    def set_status(self, status, msg=""):
        self.status = status
        self.status_message = msg

    def stop(self):
        self.stopped = True

    def update_slaves(self):
        try:
            slaves_addresses = self.nameserver.list(prefix="slave")
        except Pyro4.errors.CommunicationError as e:
            logging.exception("Nameserver communication error!")
            self.set_status(SlaveManager.STATUS_OFFLINE, "NS communication error: %s" % (e))
            self.slaves = {}
            return

        logging.info("Updating slaves %s ..." % (slaves_addresses))
        for name, address in slaves_addresses.items():
            if name in self.slaves:
                continue

            self.slaves[name] = Pyro4.Proxy(address)

        offline_slaves = [x for x in self.slaves.keys() if x not in slaves_addresses.keys()]
        for slave_name in offline_slaves:
            del self.slaves[slave_name]

        self.set_status(SlaveManager.STATUS_ONLINE)
