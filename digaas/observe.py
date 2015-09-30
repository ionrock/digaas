import time

from digaas.models import Observer
import digaas.digdig as digdig

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

def spawn_observer(observer):
    observer.status = Observer.STATUSES.PENDING
    check_function = CHECK_FUNCTIONS[observer.type]



#async def observer_main(observer, checker):
#    end_time = None
#    start = time.time()
#    while time.time() - start < observer.timeout:
#        try:
#


