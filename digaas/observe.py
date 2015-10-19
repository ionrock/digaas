import logging
import time

import gevent

from digaas.models import Observer
from digaas.storage import Storage
import digaas.digdig as digdig

LOG = logging.getLogger(__name__)

def is_zone_created(observer):
    return digdig.zone_exists(observer.name, observer.nameserver)

def is_zone_deleted(observer):
    return not is_zone_created(observer)

def is_zone_updated(observer):
    serial = digdig.get_serial(observer.name, observer.nameserver)
    return serial is not None and serial >= observer.serial

def does_record_data_match(observer):
    data = digdig.get_record_data(observer.name, observer.nameserver,
                                  observer.rdatatype)
    return data == observer.rdata

def is_record_created(observer):
    return does_record_data_match(observer)

def is_record_updated(observer):
    return does_record_data_match(observer)

def is_record_deleted(observer):
    # TODO: what if multiple records under the same name?
    # need to grab all the records and check that none match the rdata
    return not digdig.record_exists(observer.name, observer.nameserver,
                                    observer.rdatatype)

CHECK_FUNCTIONS = {
    Observer.TYPES.ZONE_CREATE: is_zone_created,
    Observer.TYPES.ZONE_UPDATE: is_zone_updated,
    Observer.TYPES.ZONE_DELETE: is_zone_deleted,
    Observer.TYPES.RECORD_CREATE: is_record_created,
    Observer.TYPES.RECORD_UPDATE: is_record_updated,
    Observer.TYPES.RECORD_DELETE: is_record_deleted,
}


def finish_observer(observer, end_time):
    if end_time is not None:
        observer.status = Observer.STATUSES.COMPLETE
        observer.duration = end_time - observer.start_time
    else:
        observer.status = Observer.STATUSES.ERROR
        observer.duration = None
    LOG.info('Observer is done %s', observer)


def run_observer(observer, check_function):
    LOG.info('Starting observer %s', observer)
    end_time = None
    start = time.time()
    while time.time() - start < observer.timeout:
        try:
            if check_function(observer):
                end_time = time.time()
                break
        except dns.exception.Timeout as e:
            print 'dns.query.udp timed out'
        except Exception as e:
            print e
            break
        time.sleep(observer.interval)
    finish_observer(observer, end_time)
    Storage.update(observer)


def spawn_observer(observer):
    observer.status = Observer.STATUSES.ACCEPTED
    observer = Storage.create(observer)
    check_function = CHECK_FUNCTIONS[observer.type]
    gevent.spawn(run_observer, observer, check_function)
    return observer

