import time
import os
import textwrap
import subprocess

from digaas.digdig import dig
import rndc

NAMESERVER = '127.0.0.1'
ZONE_FILE_DIR = '/var/cache/bind'
DEBUG = False

def generate_zone_file(zone_name, serial=None, ip=None):
    """Return a zone file string with:
        - A SOA record with the given serial, or current timestamp if None
        - An NS record for ns1.{zone_name}
        - An A record for ns1.{zone_name} pointing to 2.3.4.5
        - An A record for {zone_name} pointing to {ip}, or 1.2.3.4 if ip is None
    """
    assert zone_name and zone_name[-1] == '.'

    serial = serial or int(time.time())
    ip = ip or '1.2.3.4'

    text = textwrap.dedent("""
    $TTL 300
    {zone} IN SOA ns1.{zone} admin.{zone} {serial} 1000 1001 1002 1003
    {zone} IN NS ns1.{zone}
    ns1.{zone} IN A 2.3.4.5
    {zone} IN A {ip}
    """.format(zone=zone_name, serial=serial, ip=ip)).lstrip()
    return text

def get_zone_filename(zone_name):
    assert zone_name and zone_name[-1] == '.'
    return zone_name + 'zone'

def write_zone_file(filename, filetext):
    if DEBUG: print "Writing zone file {0}".format(filename)
    assert filename and filename.endswith('zone')
    fullpath = os.path.join(ZONE_FILE_DIR, filename)
    if DEBUG: print "   fullpath is {0}".format(fullpath)
    if DEBUG: print filetext
    with open(fullpath, 'w') as f:
        f.write(filetext)

def add_new_zone_to_bind(zone_name, serial=None, ip=None):
    """
    - Generate the zone file at /var/cache/bind/<zone_name>.zone
        - The SOA will have the given serial or the current timestamp
        - An A record for {zone_name} is added with the given ip (or 1.2.3.4 if None)
    - rndc addzone the zone
    - dig the zone to make sure it exists
    """
    zone_file = get_zone_filename(zone_name)
    zone_file_text = generate_zone_file(zone_name, serial=serial, ip=ip)
    write_zone_file(zone_file, zone_file_text)
    rndc.addzone(zone_name, zone_file)
    resp = dig(zone_name, NAMESERVER, "SOA", 5)
    if DEBUG: print resp

def _parse_soa_serial(zone_file_text):
    soa = next(x for x in zone_file_text.split('\n') if 'SOA' in x)
    if DEBUG: print 'parse_soa: found SOA record: %s' % soa

    serial = int(soa.split()[5])
    if DEBUG: print 'parse_soa: found serial number: %s' % serial

    return serial

def touch_zone(zone_name):
    """
    - Find the zone file at /var/cache/bind/<zone_name>.zone
    - Parse out the serial from the zone file
    - Rewrite the zone file with the updated serial
    - rndc reload the zone
    """
    zone_file = get_zone_filename(zone_name)
    fullpath = os.path.join(ZONE_FILE_DIR, zone_file)
    if not os.path.exists(fullpath):
        raise Exception("touch_zone: zone file '%s' not found" % fullpath)

    zone_file_text = open(fullpath, 'r').read()
    if DEBUG: print 'touch_zone: read zone file %s\n%s' % (fullpath, zone_file_text)

    serial = _parse_soa_serial(zone_file_text)
    serial += 1
    if DEBUG: print 'touch_zone: new_serial is %s' % serial

    new_zone_file_text = generate_zone_file(zone_name, serial=serial)
    write_zone_file(zone_file, new_zone_file_text)
    rndc.reload(zone_name)

def update_zone(zone_name, serial, ip):
    zone_file_text = generate_zone_file(zone_name, serial=serial, ip=ip)
    zone_file = get_zone_filename(zone_name)
    write_zone_file(zone_file, zone_file_text)
    rndc.reload(zone_name)
