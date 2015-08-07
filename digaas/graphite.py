import time
import gevent
from gevent.queue import Queue
from gevent.socket import socket

graphite_queue = None


def graphite_worker(host, port):
    """The worker pops each item off the queue and sends it to graphite."""
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

def push_query_time(response_time):
    if graphite_queue is None:
        return
    message = "digaas.query.response_time {0} {1}\n".format(
        response_time, int(time.time()))
    graphite_queue.put(message)

def setup(host, port):
    gevent.spawn(graphite_worker, host, port)
