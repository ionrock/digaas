import time
import gevent
from gevent.queue import Queue
from gevent.socket import socket

graphite_queue = None


def graphite_worker(host, port):
    """The worker pops each item off the queue and sends it to graphite."""
    global graphite_queue
    sock = socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print "Failed to connect to Graphite at {0}:{1}".format(host, port)
        return

    print "Connected to graphite at {0}:{1}".format(host, port)
    graphite_queue = Queue()

    while True:
        data = graphite_queue.get()
        print "graphite_worker: got data {0!r}".format(data)
        sock.sendall(data)


def setup(host, port):
    gevent.spawn(graphite_worker, host, port)


def push_query_time(nameserver, response_time):
    if graphite_queue is None:
        return
    nameserver = nameserver.replace('.', '-')
    timestamp = int(time.time())
    message = "digaas.query.response_time.{0} {1} {2}\n".format(
        nameserver, response_time, timestamp)
    message += "digaas.query.count.{0} {1} {2}\n".format(
        nameserver, 1, timestamp)
    graphite_queue.put(message)


def push_update_data(nameserver, duration):
    if graphite_queue is None:
        return
    nameserver = nameserver.replace('.', '-')
    timestamp = int(time.time())
    message = "digaas.updates.response_time.{0} {1} {2}\n".format(
        nameserver, duration, timestamp)
    message += "digaas.updates.count.{0} {1} {2}\n".format(
        nameserver, 1, timestamp)
    graphite_queue.put(message)


def push_delete_data(nameserver, duration):
    if graphite_queue is None:
        return
    nameserver = nameserver.replace('.', '-')
    timestamp = int(time.time())
    message = "digaas.deletes.response_time.{0} {1} {2}\n".format(
        nameserver, int(duration), timestamp)
    message += "digaas.deletes.count.{0} {1} {2}\n".format(
        nameserver, 1, timestamp)
    graphite_queue.put(message)


def push_timeout_data(nameserver):
    if graphite_queue is None:
        return
    nameserver = nameserver.replace('.', '-')
    timestamp = int(time.time())
    message = "digaas.timeouts.count.{0} {1} {2}\n".format(
        nameserver, 1, timestamp)
    graphite_queue.put(message)


def push_error_data():
    if graphite_queue is None:
        return
    timestamp = int(time.time())
    message = "digaas.errors {0} {1}\n".format(1, timestamp)
    graphite_queue.put(message)
