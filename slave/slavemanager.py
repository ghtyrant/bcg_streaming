import Pyro4
import threading
import time


class SlaveManager:
    def __init__(self):
        self.nameserver = Pyro4.locateNS()
        self.slaves = {}

        self.update_thread = threading.Thread(target=self.thread_update_slaves)
        self.update_thread.start()

        self.update_slaves()

    def thread_update_slaves(self):
        while True:
            self.update_slaves()
            time.sleep(5)

    def update_slaves(self):
        slaves_addresses = self.nameserver.list(prefix="slave")

        for name, address in slaves_addresses.items():
            if name in self.slaves:
                continue

            self.slaves[name] = Pyro4.Proxy(address)
