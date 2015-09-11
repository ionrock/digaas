import time

import gevent
import dns.exception

from digaas import digdig
from digaas.config import CONFIG as config
from digaas import storage

from consts import Status, Condition


def receive(poll_req):
    poll_req.status = Status.ACCEPTED
    storage.create_poll_request(poll_req)
    if poll_req.condition.startswith(Condition.DATA_EQUALS):
        gevent.spawn(_handle_poll_request, poll_req, _data_equals_check)
    elif poll_req.condition == Condition.SERIAL_NOT_LOWER:
        gevent.spawn(_handle_poll_request, poll_req, _serial_not_lower_check)
    elif poll_req.condition == Condition.ZONE_REMOVED:
        gevent.spawn(_handle_poll_request, poll_req, _zone_removed_check)


def finish_request(poll_req, end_time):
    if end_time is not None:
        poll_req.status = Status.COMPLETED
        poll_req.duration = end_time - poll_req.start_time
    else:
        poll_req.status = Status.ERROR
        poll_req.duration = None


def _handle_poll_request(poll_req, function):
    """
    :param function: a function that returns True when we're done polling.
        this function accepts the PollRequest as a parameter.
    """
    end_time = None
    start = time.time()
    while time.time() - start < poll_req.timeout:
        try:
            if function(poll_req):
                end_time = time.time()
                break
        except dns.exception.Timeout as e:
            print 'dns.query.udp timed out'
        except Exception as e:
            print e
            break
        gevent.sleep(seconds=poll_req.frequency)
    finish_request(poll_req, end_time)
    storage.update_poll_request(poll_req)


def _serial_not_lower_check(poll_req):
    """Return True if the zone's serial is not lower than poll_req's value"""
    serial = digdig.get_serial(poll_req.query_name, poll_req.nameserver,
        config.dns_query_timeout
    )
    return serial is not None and serial >= poll_req.serial


def _zone_removed_check(poll_req):
    """Return True if the zone is absent from the nameserver"""
    zone_found = digdig.zone_exists(poll_req.query_name,
        poll_req.nameserver, config.dns_query_timeout
    )
    return not zone_found


def _data_equals_check(poll_req):
    """Return True if the record's data matches the poll_req's value"""
    expected_data = poll_req.condition.lstrip(Condition.DATA_EQUALS)
    record_data = digdig.get_record_data(poll_req.query_name,
        poll_req.nameserver, poll_req.rdatatype, config.dns_query_timeout
    )
    return record_data == expected_data
