import redis
import uuid

import model

REDIS_CLIENT = None
def get_redis_client():
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        REDIS_CLIENT = redis.StrictRedis()
        REDIS_CLIENT.ping()  # fail fast; raises an exception if bad connection
    return REDIS_CLIENT

def fmt_value(data):
    """Format the given data as a string to store in redis.

    :param data: A dictionary as returned by PollRequest.to_dict()
    :return: A string to store as a value in redis
    """
    return ("{status} {zone_name} {serial} {nameserver} {start_time} {duration} {condition}"
            .format(**data))

def parse_value(val):
    """This undoes the result of fmt_value.

    :param val: A string, as returned by fmt_value()
    :returns: A dictionary parsed from the given val
    """

    def cvt(thing, type=None):
        """Convert "None" to None. Convert thing to the type, if provided"""
        if thing == "None":
            return None
        elif thing is not None and type is not None:
            return type(thing)
        return thing

    parts = val.split(' ')
    return {
        "status":     cvt(parts[0]),
        "zone_name":  cvt(parts[1]),
        "serial":     cvt(parts[2], type=int),
        "nameserver": cvt(parts[3]),
        "start_time": cvt(parts[4], type=float),
        "duration":   cvt(parts[5], type=float),
        "condition":  cvt(parts[6]),
    }

def create_poll_request(poll_req):
    r = get_redis_client()
    return r.set(poll_req.id, fmt_value(poll_req.to_dict()))

def update_poll_request(poll_req):
    return create_poll_request(poll_req)

def get_poll_request(id):
    r = get_redis_client()
    val = r.get(id)
    if val is not None:
        return model.PollRequest(id=id, **parse_value(val))

