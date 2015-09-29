import logging
import json
from threading import Thread, Semaphore

class LogDispatchSubscriber:
    def __init__(self):
        print("Creating LogDispatchSubscriber ...")
        self.semaphore = Semaphore(1)
        self.messages = []

    def wait(self):
        self.semaphore.acquire()
        msg = list(self.messages)
        self.messages = []
        return msg

    def emit(self, msg):
        self.messages.append(msg)
        self.semaphore.release()


class LogDispatchHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.subscriber = []

    def emit(self, record):
        for subscriber in self.subscriber:
            subscriber.emit(self.format(record))

    def subscribe(self, subscriber):
        self.subscriber.append(subscriber)
        #logging.warn("Add new log subscriber (%d total)" % (len(self.subscriber)))

    def unsubscribe(self, subscriber):
        self.subscriber.remove(subscriber)
        #logging.warn("Remove log subscriber (%d total)" % (len(self.subscriber)))
