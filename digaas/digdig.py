import time

import dns
import dns.exception
import dns.query

from digaas import graphite
from digaas.config import cfg


def prepare_query(zone_name, rdatatype):
    dns_message = dns.message.make_query(zone_name, rdatatype)
    dns_message.set_opcode(dns.opcode.QUERY)
    return dns_message


def dig(zone_name, nameserver, rdatatype):
    query = prepare_query(zone_name, rdatatype)
    start = time.time()

    result = None
    try:
        result = dns.query.udp(query, nameserver,
                               timeout=cfg.CONF.digaas.dns_query_timeout)
    except dns.exception.Timeout:
        diff = time.time() - start
        graphite.publish_query_timeout(nameserver, diff)
        raise

    diff = time.time() - start
    graphite.publish_query_success(nameserver, diff)
    return result


def get_serial(zone_name, nameserver):
    """Possibly raises dns.exception.Timeout or dns.query.BadResponse.
    Possibly returns None if, e.g., the answer section is empty."""
    resp = dig(zone_name, nameserver, dns.rdatatype.SOA)
    if not resp.answer:
        return None
    rdataset = resp.answer[0].to_rdataset()
    if not rdataset:
        return None
    return rdataset[0].serial


def record_exists(name, nameserver, rdatatype):
    """Return True if the record is found. False otherwise."""
    resp = dig(name, nameserver, rdatatype)
    return bool(resp.answer)


def zone_exists(zone_name, nameserver):
    """Return True if the zone is found on the nameserver. False otherwise."""
    return record_exists(zone_name, nameserver, dns.rdatatype.SOA)


def get_record_data(name, nameserver, rdatatype):
    """Return the data field for the given record, or None"""
    resp = dig(name, nameserver, rdatatype)
    if not resp.answer:
        return None
    rdataset = resp.answer[0].to_rdataset()
    if not rdataset:
        return None
    rdata = rdataset[0]

    # dnspython uses different attributes depending on the record type...
    if hasattr(rdata, 'address'):  # for an A record
        return str(rdata.address)
    elif hasattr(rdata, 'target'):  # for an NS record
        return str(rdata.target)
    else:
        # TODO: actual logging
        print("WARNING: failed to find data for %s record type non-empty resp:"
              % rdatatype)
        print(resp)
    return None
