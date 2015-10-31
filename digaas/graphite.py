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


def publish(message):
    if graphite_queue is None:
        return
    return graphite_queue.put(message)


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
    publish(message)


def get_query_metric_name(nameserver):
    nameserver = nameserver.replace('.', '-')
    return "digaas.queries.{0}".format(nameserver)


def publish_query_success(nameserver, response_time):
    metric = get_query_metric_name(nameserver)
    timestamp = int(time.time())
    message = "{metric}.response_time {value} {timestamp}\n".format(
        metric=metric,
        value=response_time,
        timestamp=timestamp,
    )
    message += "{metric}.success_count 1 {timestamp}\n".format(
        metric=metric,
        timestamp=timestamp,
    )
    publish(message)


def publish_query_timeout(nameserver, timeout):
    metric = get_query_metric_name(nameserver)
    timestamp = int(time.time())
    message = "{metric}.timeout {value} {timestamp}\n".format(
        metric=metric,
        value=timeout,
        timestamp=timestamp,
    )
    message += "{metric}.timeout_count 1 {timestamp}\n".format(
        metric=metric,
        timestamp=timestamp,
    )
    publish(message)
