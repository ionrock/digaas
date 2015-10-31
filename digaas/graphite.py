import logging
import time

import gevent
from gevent.queue import Queue
from gevent.socket import socket

graphite_queue = None

LOG = logging.getLogger(__name__)


def graphite_worker(host, port):
    """The worker pops each item off the queue and sends it to graphite."""
    global graphite_queue
    sock = socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        LOG.error("Failed to connect to Graphite at %s:%s", host, port)
        LOG.exception(e)
        return

    LOG.info("Connected to graphite at %s:%s", host, port)
    graphite_queue = Queue()

    while True:
        data = graphite_queue.get()
        LOG.debug("graphite_worker received data: {0!r}".format(data))
        sock.sendall(data)


def setup(host, port):
    gevent.spawn(graphite_worker, host, port)


def publish_observer_data(observer):
    metric = "digaas.observers.{0}".format(observer.type)
    timestamp = int(time.time())
    if observer.status == observer.STATUSES.COMPLETE:
        message = "{metric}.duration {value} {timestamp}\n".format(
            metric=metric,
            value=observer.duration,
            timestamp=timestamp,
        )
        message += "{metric}.success_count 1 {timestamp}\n".format(
            metric=metric,
            timestamp=timestamp,
        )
    else:
        message = "{metric}.error_count 1 {timestamp}\n".format(
            metric=metric,
            timestamp=timestamp,
        )
    graphite_queue.put(message)
