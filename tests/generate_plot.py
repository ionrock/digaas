import random
import time

import gevent
import gevent.monkey
import requests

import tools, rndc
import datagen
from client import DigaasClient

gevent.monkey.patch_time()

client = DigaasClient('http://127.0.0.1')
NAMESERVER = tools.NAMESERVER

def generate_datapoint():
    zone_name = datagen.random_zone_name()
    serial = 123456
    tools.add_new_zone_to_bind(zone_name, serial=serial)

    # ask digaas to poll for the zone until it sees serial + 1 (or greater)
    resp = client.post_poll_request(
        query_name = zone_name,
        nameserver = NAMESERVER,
        serial = serial + 1,
        condition = client.SERIAL_NOT_LOWER,
        start_time = time.time(),
        timeout = 15,
        frequency = 1)
    assert resp.status_code == 202
    id = resp.json()['id']

    # wait a bit before updating the serial number by 1
    duration = random.randint(2, 10)
    time.sleep(duration)
    tools.touch_zone(zone_name)

    # wait for digaas to finish polling
    client.wait_for_completed_poll_request(id)
    resp = client.get_poll_request(id)

    print "Generated datapoint for serial update {0}: {1} {2}".format(
        resp.json()['query_name'],
        resp.json()['start_time'],
        resp.json()['duration']
    )

def generate_zone_deleted():
    zone_name = datagen.random_zone_name()
    serial = 123456
    tools.add_new_zone_to_bind(zone_name, serial=serial)

    # ask digaas to poll for the zone until it disappears from the nameserver
    resp = client.post_poll_request(
        query_name = zone_name,
        nameserver = NAMESERVER,
        serial = 0,
        condition = client.ZONE_REMOVED,
        start_time = time.time(),
        timeout = 15,
        frequency = 1)
    assert resp.status_code == 202
    id = resp.json()['id']

    # wait a bit before removing the zone
    duration = random.randint(2, 10)
    time.sleep(duration)
    rndc.delzone(zone_name)

    # wait for digaas to finish polling
    client.wait_for_completed_poll_request(id)
    resp = client.get_poll_request(id)

    print "Generated datapoint for zone removed {0}: {1} {2}".format(
        resp.json()['query_name'],
        resp.json()['start_time'],
        resp.json()['duration']
    )

# generate a number of datapoints to plot
START = int(time.time() - 1)
threads = [gevent.spawn(generate_datapoint) for _ in xrange(200)] \
        + [gevent.spawn(generate_zone_deleted) for _ in xrange(200)]
gevent.wait(threads)
END = int(time.time() + 1)

# ask digaas to generate the plot
resp = client.post_stats_request(START, END)
print resp
id = resp.json()['id']
client.wait_for_completed_stats_request(id)

resp = client.get_stats_request(id)
print "/stats/{0}".format(resp.json()['id'])
print "/images/{0}".format(resp.json()['image_id'])
