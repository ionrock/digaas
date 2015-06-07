import json
import requests
import time
import unittest

import client
import tools
import rndc
import datagen
import digaas.digdig as dig

NAMESERVER = tools.NAMESERVER

class TestPolling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPolling, cls).setUpClass()
        cls.client = client.DigaasClient('http://127.0.0.1')

    def test_get_version(self):
        resp = self.client.get_version()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['service'], 'digaas')

    def test_poll_for_serial_not_lower(self):
        # add a random zone to the nameserver with a known serial
        zone_name = datagen.random_zone_name()
        serial = 123456
        tools.add_new_zone_to_bind(zone_name, serial=serial)
        self.assertTrue(dig.zone_exists(zone_name, NAMESERVER))
        self.assertEqual(dig.get_serial(zone_name, NAMESERVER), serial)

        # ask digaas to poll for the zone until it sees serial + 1 (or greater)
        resp = self.client.post_poll_request(
            query_name = zone_name,
            nameserver = NAMESERVER,
            serial = serial + 1,
            condition = self.client.SERIAL_NOT_LOWER,
            start_time = time.time(),
            timeout = 15,
            frequency = 1)
        self.assertEqual(resp.status_code, 202)
        id = resp.json()['id']

        # wait two seconds before we increment the serial by one
        min_duration = 2
        time.sleep(min_duration)
        tools.touch_zone(zone_name)

        # wait for the digaas to finish polling
        self.client.wait_for_completed_poll_request(id)
        resp = self.client.get_poll_request(id)

        # check the entire response body
        self.assertGreater(resp.json()['duration'], min_duration)
        self.assertEqual(resp.json()['query_name'], zone_name)
        self.assertEqual(resp.json()['serial'], serial + 1)
        self.assertEqual(resp.json()['nameserver'], NAMESERVER)
        self.assertEqual(resp.json()['frequency'], 1)
        self.assertEqual(resp.json()['timeout'], 15)
        self.assertEqual(resp.json()['condition'], self.client.SERIAL_NOT_LOWER)
        self.assertEqual(resp.json()['rdatatype'], None)
        self.assertEqual(resp.json()['status'], 'COMPLETED')
        self.assertEqual(resp.json()['id'], id)

    def test_timeout_on_polling_for_serial(self):
        # add a random zone to the nameserver with a known serial
        zone_name = datagen.random_zone_name()
        serial = 123456
        tools.add_new_zone_to_bind(zone_name, serial=serial)

        # ask digaas to poll for the zone until it sees serial + 1, which will never happen
        resp = self.client.post_poll_request(
            query_name = zone_name,
            nameserver = NAMESERVER,
            serial = serial + 1,
            condition = self.client.SERIAL_NOT_LOWER,
            start_time = time.time(),
            timeout = 4,
            frequency = 1)
        self.assertEqual(resp.status_code, 202)
        id = resp.json()['id']

        # wait for the digaas to timeout on the poll request
        self.client.wait_for_errored_poll_request(id)
        resp = self.client.get_poll_request(id)

        # check the entire response body
        self.assertEqual(resp.json()['duration'], None)
        self.assertEqual(resp.json()['query_name'], zone_name)
        self.assertEqual(resp.json()['serial'], serial + 1)
        self.assertEqual(resp.json()['nameserver'], NAMESERVER)
        self.assertEqual(resp.json()['frequency'], 1)
        self.assertEqual(resp.json()['timeout'], 4)
        self.assertEqual(resp.json()['condition'], self.client.SERIAL_NOT_LOWER)
        self.assertEqual(resp.json()['rdatatype'], None)
        self.assertEqual(resp.json()['status'], 'ERROR')
        self.assertEqual(resp.json()['id'], id)

    def test_poll_for_zone_removed(self):
        # add a random zone to the nameserver with a known serial
        zone_name = datagen.random_zone_name()
        tools.add_new_zone_to_bind(zone_name)

        # ask digaas to poll until the zone is removed from the nameserver
        resp = self.client.post_poll_request(
            query_name = zone_name,
            nameserver = NAMESERVER,
            serial = 0,
            condition = self.client.ZONE_REMOVED,
            start_time = time.time(),
            timeout = 15,
            frequency = 1)
        self.assertEqual(resp.status_code, 202)
        id = resp.json()['id']

        # wait two seconds before we remove the zone
        min_duration = 2
        time.sleep(min_duration)
        tools.touch_zone(zone_name)

        rndc.delzone(zone_name)

        # wait for the digaas to timeout on the poll request
        self.client.wait_for_completed_poll_request(id)
        resp = self.client.get_poll_request(id)

        # check the entire response body
        self.assertGreater(resp.json()['duration'], min_duration)
        self.assertEqual(resp.json()['query_name'], zone_name)
        self.assertEqual(resp.json()['nameserver'], NAMESERVER)
        self.assertEqual(resp.json()['frequency'], 1)
        self.assertEqual(resp.json()['timeout'], 15)
        self.assertEqual(resp.json()['condition'], self.client.ZONE_REMOVED)
        self.assertEqual(resp.json()['rdatatype'], None)
        self.assertEqual(resp.json()['status'], 'COMPLETED')
        self.assertEqual(resp.json()['id'], id)

    def test_timeout_on_polling_for_removed_zone(self):
        # add a random zone to the nameserver with a known serial
        zone_name = datagen.random_zone_name()
        tools.add_new_zone_to_bind(zone_name)

        # ask digaas to poll until the zone is removed from the nameserver,
        # which will never happen
        resp = self.client.post_poll_request(
            query_name = zone_name,
            nameserver = NAMESERVER,
            serial = 0,
            condition = self.client.ZONE_REMOVED,
            start_time = time.time(),
            timeout = 4,
            frequency = 1)
        self.assertEqual(resp.status_code, 202)
        id = resp.json()['id']

        # wait for the digaas to timeout on the poll request
        self.client.wait_for_errored_poll_request(id)
        resp = self.client.get_poll_request(id)

        # check the entire response body
        self.assertEqual(resp.json()['duration'], None)
        self.assertEqual(resp.json()['query_name'], zone_name)
        self.assertEqual(resp.json()['nameserver'], NAMESERVER)
        self.assertEqual(resp.json()['frequency'], 1)
        self.assertEqual(resp.json()['timeout'], 4)
        self.assertEqual(resp.json()['condition'], self.client.ZONE_REMOVED)
        self.assertEqual(resp.json()['rdatatype'], None)
        self.assertEqual(resp.json()['status'], 'ERROR')
        self.assertEqual(resp.json()['id'], id)
