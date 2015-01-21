import time

import gevent
import dns.exception

import digdig
import digaas_config as config
from digaas_config import storage


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
    poll_req.status = Status.ACCEPTED
    storage.create_poll_request(poll_req)
    if poll_req.condition == Conditions.SERIAL_NOT_LOWER:
        thing = gevent.spawn(_handle_serial_not_lower, poll_req)
    elif poll_req.condition == Conditions.ZONE_REMOVED:
        thing = gevent.spawn(_handle_zone_removed, poll_req)
    # what to do with thing?


def _handle_serial_not_lower(poll_req):
    """Handle a poll request to check that the serial number of the zone is not
    lower than the provided poll_req.serial. This is used for checking newly
    created and updated zones.

    :param poll_req: The PollRequest to handle.
    """
    start = time.time()
    serial = None
    end_time = None
    while time.time() - start < poll_req.timeout:
        try:
            serial = digdig.get_serial(poll_req.zone_name, poll_req.nameserver,
                config.dns_query_timeout
            )
            if serial is not None and serial >= poll_req.serial:
                end_time = time.time()
                break
        except dns.exception.Timeout as e:
            print 'dns.query.udp timed out'
        except Exception as e:
            print e
            break
        # ensure we yield to other greenlets
        gevent.sleep(seconds=poll_req.frequency)
    print "serial_not_lower loop done"
    if serial is not None and end_time is not None:
        poll_req.status = Status.COMPLETED
        poll_req.duration = end_time - poll_req.start_time
    else:
        poll_req.status = Status.ERROR
        poll_req.duration = None
    storage.update_poll_request(poll_req)


def _handle_zone_removed(poll_req):
    """Handle a poll request to check that a zone is absent from
    poll_req.nameserver"""
    start = time.time()
    end_time = None
    while time.time() - start < poll_req.timeout:
        try:
            zone_found = digdig.zone_exists(poll_req.zone_name,
                poll_req.nameserver, config.dns_query_timeout
            )
            if not zone_found:
                end_time = time.time()
                break
        except dns.exception.Timeout as e:
            print 'dns.query.udp timed out'
        except Exception as e:
            print e
            break
        # ensure we yield to other greenlets
        gevent.sleep(seconds=poll_req.frequency)

    if end_time is not None:
        poll_req.status = Status.COMPLETED
        poll_req.duration = end_time - poll_req.start_time
    else:
        poll_req.status = Status.ERROR
        poll_req.duration = None
    storage.update_poll_request(poll_req)
