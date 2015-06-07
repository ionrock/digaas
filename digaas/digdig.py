import dns
import dns.exception
import dns.query

def prepare_query(zone_name, rdatatype):
    dns_message = dns.message.make_query(zone_name, rdatatype)
    dns_message.set_opcode(dns.opcode.QUERY)
    return dns_message

def dig(zone_name, nameserver, rdatatype, timeout):
    query = prepare_query(zone_name, rdatatype)
    return dns.query.udp(query, nameserver, timeout=timeout)

def get_serial(zone_name, nameserver, timeout=1):
    """Possibly raises dns.exception.Timeout or dns.query.BadResponse.
    Possibly returns None if, e.g., the answer section is empty."""
    resp = dig(zone_name, nameserver, dns.rdatatype.SOA, timeout=timeout)
    if not resp.answer:
        return None
    rdataset = resp.answer[0].to_rdataset()
    if not rdataset:
        return None
    return rdataset[0].serial

def zone_exists(zone_name, nameserver, timeout=1):
    """Return True if the zone is found on the nameserver. False otherwise."""
    resp = dig(zone_name, nameserver, dns.rdatatype.SOA, timeout=timeout)
    return bool(resp.answer)

def get_record_data(name, nameserver, rdatatype, timeout=1):
    """Return the data field for the given record, or None"""
    resp = dig(name, nameserver, rdatatype, timeout=timeout)
    if not resp.answer:
        return None
    rdataset = resp.answer[0].to_rdataset()
    if not rdataset:
        return None
    rdata = rdataset[0]

    # dnspython stores data in different attributes depending on the record type...
    if hasattr(rdata, 'address'):  # for an A record
        return str(rdata.address)
    elif hasattr(rdata, 'target'): # for an NS record
        return str(rdata.target)
    else:
        print "WARNING: failed to find data for %s record type non-empty resp:" % rdatatype
        print resp
    return None
