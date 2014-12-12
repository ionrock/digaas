import redis
import uuid

import model

REDIS_CLIENT = None
def get_redis_client():
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        REDIS_CLIENT = redis.StrictRedis()
        REDIS_CLIENT.ping()  # fail fast - raise exception if bad connection
    return REDIS_CLIENT


def fmt_value(poll_req):
    return ("{status} {zone_name} {serial} {nameserver} {start_time} {duration}"
            .format(**poll_req.to_dict()))

def parse_value(val):
    parts = val.split(' ')

    def cvt(part, type=None):
        part = part if part != "None" else None
        if part is not None and type is not None:
            return type(part)
        return part

    return {
        "status":     cvt(parts[0]),
        "zone_name":  cvt(parts[1]),
        "serial":     cvt(parts[2], type=int),
        "nameserver": cvt(parts[3]),
        "start_time": cvt(parts[4], type=float),
        "duration":   cvt(parts[5], type=float),
    }

def create_entry(poll_req):
    r = get_redis_client()
    return r.set(poll_req.id, fmt_value(poll_req))

def update_entry(poll_req):
    return create_entry(poll_req)

def get_entry(id):
    r = get_redis_client()
    val = r.get(id)
    if val is not None:
        return model.PollRequest(id=id, **parse_value(val))

