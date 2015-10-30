import os
import Pyro4
import threading
import time
import logging
import psutil
import base64
from PIL import Image

class SlaveWrapper(object):
    def __init__(self, name, address, obj):
        self._wrapped_obj = obj
        self.name = name
        self.address = address
        self.last_ping = time.time()

    def __getattr__(self, attr):
        # see if this object has attr
        # NOTE do not use hasattr, it goes into
        # infinite recurrsion
        if attr in self.__dict__:
            return getattr(self, attr)

        return getattr(self._wrapped_obj, attr)

    def __str__(self):
        return "<Slave (%s, %s)>" % (self.name, self.address)

class SlaveManager:
    STATUS_OFFLINE = 0
    STATUS_ONLINE = 1

    def __init__(self, base_url, base_dir):
        self.nameserver = Pyro4.locateNS()
        self.slaves = {}

        self.set_status(SlaveManager.STATUS_OFFLINE, "Starting up ...")

        self.stopped = False

        self.update_thread = threading.Thread(target=self.thread_update_slaves)
        self.update_thread.start()

        self.bytes_sent = 0
        self.bytes_received = 0
        self.speed_up = 0
        self.speed_down = 0
        self.traffic_last_check = 0

        self.base_url = base_url
        self.base_dir = base_dir

    def get_stream_list(self):
        return [(x, self.get_stream_url(x)) for x in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, x)) and os.path.exists(os.path.join(os.path.join(self.base_dir, x), "out.m3u8"))]

    def get_stream_url(self, stream):
        return "%s/%s/out.m3u8" % (self.base_url, stream)

    def thread_update_slaves(self):
        while not self.stopped:
            self.update_slaves()
            traffic = psutil.net_io_counters()
            self.set_traffic(traffic.bytes_sent, traffic.bytes_recv)

            for name, slave in self.slaves.iteritems():
                try:
                    self.fetch_slave_screenshot(name)
                except Pyro4.errors.CommunicationError as e:
                    logging.exception("Error communicating with slave!")
                    continue

            time.sleep(5)

    def get_slave_by_name(self, name):
        return self.slaves.get(name, None)

    def get_all_slaves(self):
        return self.slaves.values()

    def fetch_slave_screenshot(self, slave_name):
        slave = self.slaves[slave_name]
        img_data = slave.get_screenshot()

        if not img_data or "error" in img_data:
            return

        img_data['data'] = base64.b64decode(img_data['data'])
        img = Image.frombytes(**img_data)
        img_file = open("screens/%s.jpg" % slave_name, "wb")
        img.save(img_file, 'JPEG', quality=70)

    def set_status(self, status, msg=""):
        self.status = status
        self.status_message = msg

    def stop(self):
        self.stopped = True

    def set_traffic(self, sent, received):
        self.speed_up = (sent - self.bytes_sent) / (time.time() - self.traffic_last_check)
        self.speed_down = (received - self.bytes_received) / (time.time() - self.traffic_last_check)
        self.bytes_sent = sent
        self.bytes_received = received

        self.traffic_last_check = time.time()

    def get_traffic_speed(self):
        return (self.speed_up, self.speed_down)

    def get_traffic_total(self):
        return (self.bytes_sent, self.bytes_received)

    def update_slaves(self):
        try:
            slaves_addresses = self.nameserver.list(prefix="slave")
        except Pyro4.errors.CommunicationError as e:
            logging.exception("Nameserver communication error!")
            self.set_status(SlaveManager.STATUS_OFFLINE, "NS communication error: %s" % (e))
            self.slaves = {}
            return

        print(slaves_addresses)
        for name, address in slaves_addresses.items():
            if name in self.slaves:
                try:
                    if self.slaves[name].ping() == "pong":
                        self.slaves[name].last_ping = time.time()
                except Pyro4.errors.CommunicationError as e:
                    pass

                if time.time() - self.slaves[name].last_ping > 6:
                    logging.info("Removing slave %s due to timeout ..." % (name))
                    del self.slaves[name]
                    self.nameserver.remove(name=name)
                    continue

                if address == self.slaves[name].address:
                    continue

            logging.info("Discovered new slave %s (@%s) ..." % (name, address))
            self.slaves[name] = SlaveWrapper(name, address, Pyro4.Proxy(address))

        offline_slaves = [x for x in self.slaves.keys() if x not in slaves_addresses.keys()]
        for slave_name in offline_slaves:
            logging.info("Removing slave %s ..." % (slave_name))
            del self.slaves[slave_name]

        self.set_status(SlaveManager.STATUS_ONLINE)
