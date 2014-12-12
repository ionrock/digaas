import dns
import dns.exception
import dns.query

def prepare_query(zone_name, rdatatype):
    dns_message = dns.message.make_query(zone_name, rdatatype)
    dns_message.set_opcode(dns.opcode.QUERY)
    return dns_message

def dig(zone_name, nameserver, rdatatype):
    query = prepare_query(zone_name, rdatatype)
    return dns.query.udp(query, nameserver)

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

