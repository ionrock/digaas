import time

import gevent

import digdig
import storage
import digaas_config as config


class Status:
    ACCEPTED  = "ACCEPTED"
    ERROR     = "ERROR"
    COMPLETED = "COMPLETED"


def receive(poll_req):
    # TODO: store in redis
    poll_req.status = Status.ACCEPTED
    storage.create_entry(poll_req)
    thing = gevent.spawn(_handle, poll_req)
    # what to do with thing?

def _handle(poll_req, timeout=config.timeout):
    """
    :param poll_req: The PollRequest to handle.
    :param timeout: When the PollRequest times out, in seconds.
    """
    start = time.time()
    serial = None
    end_time = None
    while time.time() - start < timeout:
        try:
            print time.time(), "querying for %s" % poll_req.zone_name
            serial = digdig.get_serial(poll_req.zone_name, poll_req.nameserver)
            if serial is not None and serial >= poll_req.serial:
                print "got serial: %s" % serial
                end_time = time.time()
                break
            elif serial is not None:
                print "got earlier serial: %s" % serial
                # TODO: what to do if found serial is *earlier* than expected?
                break
        except Exception as e:
            print "Exception: " + str(e)
            pass
        # ensure we yield to other greenlets
        gevent.sleep(seconds=config.frequency)
    print "loop done"
    if serial is not None and end_time is not None:
        poll_req.status = Status.COMPLETED
        poll_req.duration = end_time - poll_req.start_time
    else:
        poll_req.status = Status.ERROR
        poll_req.duration = None
    storage.update_entry(poll_req)
