import redis

import digaas_config as CONFIG
import model
from consts import Condition

print "USING REDIS STORAGE"

SERIAL_NOT_LOWER_SET_NAME = 'SerialNotLower_sorted_set'
ZONE_REMOVED_SET_NAME = 'ZoneRemoved_sorted_set'

REDIS_CLIENT = None
def get_redis_client():
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        REDIS_CLIENT = redis.StrictRedis(
            host=CONFIG.redis_host,
            port=CONFIG.redis_port,
            password=CONFIG.redis_password,
        )
        REDIS_CLIENT.ping()  # fail fast; raises an exception if bad connection
    return REDIS_CLIENT

def fmt_value(*data):
    """Format the given data as a string to store in redis.

    :param data: A dictionary as returned by PollRequest.to_dict()
    :return: A string to store as a value in redis
    """
    def cvt(thing):
        if thing is None:
            return "None"
        elif isinstance(thing, float):
            # ensure our floats don't noticeably lose precision
            return "{0:.17g}".format(thing)
        return thing
    return " ".join(str(cvt(x)) for x in data)

def cvt(thing, type=None):
    """Convert "None" to None. Convert thing to the type, if provided"""
    if thing == "None":
        return None
    elif thing is not None and type is not None:
        return type(thing)
    return thing

def fmt_poll_request_value(poll_req):
    return fmt_value(
        poll_req.status,
        poll_req.query_name,
        poll_req.rdatatype,
        poll_req.serial,
        poll_req.nameserver,
        poll_req.start_time,
        poll_req.duration,
        poll_req.condition,
        poll_req.timeout,
        poll_req.frequency)

def parse_poll_request_value(val):
    """This undoes fmt_poll_request_value.

    :param val: A string, as returned by fmt_poll_request_value()
    :returns: A dictionary parsed from the given val
    """
    parts = val.split(' ')
    return {
        "status":     cvt(parts[0]),
        "query_name": cvt(parts[1]),
        "rdatatype":  cvt(parts[2]),
        "serial":     cvt(parts[3], type=int),
        "nameserver": cvt(parts[4]),
        "start_time": cvt(parts[5], type=float),
        "duration":   cvt(parts[6], type=float),
        "condition":  cvt(parts[7]),
        "timeout":    cvt(parts[8], type=int),
        "frequency":  cvt(parts[9], type=float),
    }

def fmt_stats_request_value(stats_req):
    return fmt_value(
        stats_req.status,
        stats_req.start_time,
        stats_req.end_time,
        stats_req.image_id,
    )

def parse_stats_request_value(val):
    parts = val.split(' ')
    return {
        "status":     cvt(parts[0]),
        "start_time": cvt(parts[1], type=float),
        "end_time":   cvt(parts[2], type=float),
        "image_id":   cvt(parts[3]),
    }

def create_poll_request(poll_req):
    r = get_redis_client()
    return r.set(poll_req.id, fmt_poll_request_value(poll_req))

def update_poll_request(poll_req):
    # add the start_time + duration to a sorted set for fast querying to generate
    # the plot (I'm assuming this only gets called once, when the status
    # changes from ACCEPTED to COMPLETE/ERROR)
    #
    # This uses one sorted set for zone creates/updates and another for zone
    # deletes. The sets are sorted by the start_time passed to digaas by the
    # user.
    r = get_redis_client()
    if poll_req.condition == Condition.SERIAL_NOT_LOWER \
            or poll_req.condition.startswith(Condition.DATA_EQUALS):
        r.zadd(SERIAL_NOT_LOWER_SET_NAME, poll_req.start_time,
            "update {0} {1}".format(poll_req.start_time, poll_req.duration))
    elif poll_req.condition == Condition.ZONE_REMOVED:
        r.zadd(ZONE_REMOVED_SET_NAME, poll_req.start_time,
            "remove {0} {1}".format(poll_req.start_time, poll_req.duration))
    return create_poll_request(poll_req)

def get_poll_request(id):
    r = get_redis_client()
    val = r.get(id)
    if val is not None:
        return model.PollRequest(id=id, **parse_poll_request_value(val))

def create_image_filename(id, filename):
    r = get_redis_client()
    return r.set(id, filename)

def get_image_filename(id):
    r = get_redis_client()
    return r.get(id)

def select_time_range(lo, hi):
    """Select a bunch of strings which are specifically ordered by start_time.
    These strings are of the format "<operation> <serial> <duration>" where
        operation is either 'update' or 'remove'
        serial is the serial of the zone
        duration is the recorded propagation time
    """
    r = get_redis_client()
    return r.zrangebyscore(SERIAL_NOT_LOWER_SET_NAME, lo, hi) \
        + r.zrangebyscore(ZONE_REMOVED_SET_NAME, lo, hi)

def create_stats_request(stats_req):
    r = get_redis_client()
    return r.set(stats_req.id, fmt_stats_request_value(stats_req))

def update_stats_request(stats_req):
    return create_stats_request(stats_req)

def get_stats_request(id):
    r = get_redis_client()
    val = r.get(id)
    if val is not None:
        return model.StatsRequest(id=id, **parse_stats_request_value(val))

