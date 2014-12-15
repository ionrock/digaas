import time

import gevent

import digdig
import storage
import digaas_config as config


class Status:
    ACCEPTED  = "ACCEPTED"
    ERROR     = "ERROR"
    COMPLETED = "COMPLETED"


class Conditions:
    """These are used to determine when the poll request has succeeded"""
    SERIAL_NOT_LOWER = "serial_not_lower"
    ZONE_REMOVED     = "zone_removed"

    ALL = (SERIAL_NOT_LOWER, ZONE_REMOVED)


def receive(poll_req):
    # TODO: store in redis
    poll_req.status = Status.ACCEPTED
    storage.create_poll_request(poll_req)
    if poll_req.condition == Conditions.SERIAL_NOT_LOWER:
        thing = gevent.spawn(_handle_serial_not_lower, poll_req)
    elif poll_req.condition == Conditions.ZONE_REMOVED:
        thing = gevent.spawn(_handle_zone_removed, poll_req)
    # what to do with thing?


def _handle_serial_not_lower(poll_req, timeout=config.timeout):
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
        except Exception as e:
            print e
            break
        # ensure we yield to other greenlets
        gevent.sleep(seconds=config.frequency)
    print "serial_not_lower loop done"
    if serial is not None and end_time is not None:
        poll_req.status = Status.COMPLETED
        poll_req.duration = end_time - poll_req.start_time
    else:
        poll_req.status = Status.ERROR
        poll_req.duration = None
    storage.update_poll_request(poll_req)


def _handle_zone_removed(poll_req, timeout=config.timeout):
    start = time.time()
    end_time = None
    while time.time() - start < timeout:
        try:
            print time.time(), "querying for %s" % poll_req.zone_name
            serial = digdig.get_serial(poll_req.zone_name, poll_req.nameserver)
            if serial is None:
                end_time = time.time()
                break
        except Exception as e:
            print e
            break

        # ensure we yield to other greenlets
        gevent.sleep(seconds=config.frequency)

    print "zone_removed loop done"
    if end_time is not None:
        poll_req.status = Status.COMPLETED
        poll_req.duration = end_time - poll_req.start_time
    else:
        poll_req.status = Status.ERROR
        poll_req.duration = None
    storage.update_poll_request(poll_req)
