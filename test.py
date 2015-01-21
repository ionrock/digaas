import json
import random
import unittest
import string
import time

import requests

from designate_client import DesignateClient


class Datagen(object):

    @staticmethod
    def get_random_string(length):
        return "".join(random.choice(string.letters) for _ in xrange(length))

    @classmethod
    def get_random_zone(cls):
        return "{0}.{1}.com.".format(cls.get_random_string(random.randrange(2, 6)),
                                     cls.get_random_string(random.randrange(5, 30)))


class DigaasClient(object):

    SERIAL_NOT_LOWER = 'serial_not_lower'
    ZONE_REMOVED = 'zone_removed'

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def _poll_requests_url(self):
        return self.endpoint + '/requests'

    def _poll_request_url(self, id):
        return self._poll_requests_url() + '/' + str(id)

    def post_poll_request(self, zone, nameserver, serial, condition, start_time,
                          timeout, frequency):
        return requests.post(self._poll_requests_url(),
            data=json.dumps(dict(
                zone_name  = zone,
                nameserver = nameserver,
                serial     = serial,
                condition  = condition,
                start_time = start_time,
                timeout    = timeout,
                frequency  = frequency)))

    def get_poll_request(self, id):
        return requests.get(self._poll_request_url(id))


class TestPollRequest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.digaas_client = DigaasClient(endpoint='http://localhost:9090')
        cls.designate_client = DesignateClient(endpoint='http://192.168.33.20:9001')
        cls.nameserver = '192.168.33.20'

    def test_poll_request_serial_not_lower_timeout(self):
        """Check that I can:
            1. submit a poll request
            2. see the "ACCEPTED" status
            3. allow the request to timeout
            4. move into an error state
        """
        # we're assuming this zone doesn't exist on the nameserver
        zone = Datagen.get_random_zone()
        start_time = time.time()
        serial = int(time.time())
        timeout = 1
        frequency = 0.2

        def check_response_body(resp, status, duration=None, id=None):
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['serial'],     serial)
            self.assertEquals(resp.json()['condition'],  DigaasClient.SERIAL_NOT_LOWER)
            self.assertEquals(resp.json()['zone_name'],  zone)
            self.assertEquals(resp.json()['nameserver'], self.nameserver)
            self.assertEquals(resp.json()['duration'],   duration)
            self.assertEquals(resp.json()['frequency'],  frequency)
            self.assertEquals(resp.json()['timeout'],    timeout)
            if id is None:
                self.assertTrue('id' in resp.json())
            else:
                self.assertEquals(resp.json()['id'], id)

        # create the poll request
        resp = self.digaas_client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.SERIAL_NOT_LOWER,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)

        # check post response
        self.assertEquals(resp.status_code, 202)
        check_response_body(resp, status="ACCEPTED")

        id = resp.json()['id']

        # get the poll request
        resp = self.digaas_client.get_poll_request(id)
        self.assertEquals(resp.status_code, 200)
        check_response_body(resp, status="ACCEPTED", id=id)

        # wait for poll request to timeout
        time.sleep(timeout + frequency)

        resp = self.digaas_client.get_poll_request(id)
        self.assertEquals(resp.status_code, 200)
        check_response_body(resp, status="ERROR", id=id)

    def test_poll_request_serial_not_lower_completed(self):
        """Check that I can:
            1. submit a poll request
            2. see the "ACCEPTED" status
            3. allow the request to timeout
            4. move into an error state
        """
        zone = Datagen.get_random_zone()
        resp = self.designate_client.post_zone(
            name=zone, email="mickey@example.com", ttl=2400)
        self.assertEquals(resp.status_code, 201)

        start_time = time.time()
        serial = resp.json()['zone']['serial']
        timeout = 60
        frequency = 1

        def check_response_body(resp, status, id=None):
            """Does not check duration"""
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['serial'],     serial)
            self.assertEquals(resp.json()['condition'],  DigaasClient.SERIAL_NOT_LOWER)
            self.assertEquals(resp.json()['zone_name'],  zone)
            self.assertEquals(resp.json()['nameserver'], self.nameserver)
            #self.assertEquals(resp.json()['duration'],   duration)
            self.assertEquals(resp.json()['frequency'],  frequency)
            self.assertEquals(resp.json()['timeout'],    timeout)
            if id is None:
                self.assertTrue('id' in resp.json())
            else:
                self.assertEquals(resp.json()['id'], id)

        # create the poll request
        resp = self.digaas_client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.SERIAL_NOT_LOWER,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)

        # check post response
        self.assertEquals(resp.status_code, 202)
        check_response_body(resp, status="ACCEPTED")

        id = resp.json()['id']

        # poll until we see a "COMPLETED"
        start = time.time()
        while True:
            if time.time() - start > timeout + frequency:
                raise Exception("Timed out before completion")
            resp = self.digaas_client.get_poll_request(id)
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                check_response_body(resp, status="COMPLETED", id=id)
                self.assertGreater(resp.json()['duration'], 0)
                break
            else:
                time.sleep(frequency)

    def test_poll_request_zone_removed_completed(self):
        # create the zone
        zone = Datagen.get_random_zone()
        resp = self.designate_client.post_zone(
            name=zone, email="mickey@example.com", ttl=2400)
        self.assertEquals(resp.status_code, 201)
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']

        # use the thing we're testing to see if the zone gets to the nameserver?
        # this is already tested in another function.
        # create the poll request
        timeout = 10
        frequency = 1
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.SERIAL_NOT_LOWER,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)

        id = resp.json()['id']

        # poll until we see a "COMPLETED"
        start = time.time()
        while True:
            if time.time() - start > timeout + frequency:
                raise Exception("Timed out before completion")
            resp = self.digaas_client.get_poll_request(id)
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                # check_response_body(resp, status="COMPLETED", id=id)
                self.assertGreater(resp.json()['duration'], 0)
                break
            else:
                time.sleep(frequency)

        timeout = 120
        # delete the zone
        resp = self.designate_client.delete_zone(zone_id)
        self.assertEquals(resp.status_code, 204)

        # check the zone is removed
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.ZONE_REMOVED,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)

        id = resp.json()['id']

        # poll until we see a "COMPLETED"
        print "polling until completed: timeout = %s" % timeout
        start = time.time()
        while True:
            if time.time() - start > timeout + frequency:
                raise Exception("Timed out before completion")
            resp = self.digaas_client.get_poll_request(id)
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                self.assertGreater(resp.json()['duration'], 0)
                break
            else:
                time.sleep(frequency)

    def test_poll_request_zone_removed_timeout(self):
        # create the zone
        zone = Datagen.get_random_zone()
        resp = self.designate_client.post_zone(
            name=zone, email="mickey@example.com", ttl=2400)
        self.assertEquals(resp.status_code, 201)
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']
        timeout = 3
        frequency = 0.5

        def check_response_body(resp, status, condition, id=None):
            """Does not check duration"""
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['serial'],     serial)
            self.assertEquals(resp.json()['condition'],  condition)
            self.assertEquals(resp.json()['zone_name'],  zone)
            self.assertEquals(resp.json()['nameserver'], self.nameserver)
            #self.assertEquals(resp.json()['duration'],   duration)
            self.assertEquals(resp.json()['frequency'],  frequency)
            self.assertEquals(resp.json()['timeout'],    timeout)
            if id is None:
                self.assertTrue('id' in resp.json())
            else:
                self.assertEquals(resp.json()['id'], id)

        # We need to verify that the zone is on the nameserver. We can do this
        # using the service, assuming the `serial_not_lower` test cases pass
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.SERIAL_NOT_LOWER,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)

        id = resp.json()['id']

        # poll until we see a "COMPLETED", so we know the zone is on the nameserver
        start = time.time()
        while True:
            if time.time() - start > timeout + frequency:
                raise Exception("Timed out before completion")
            resp = self.digaas_client.get_poll_request(id)
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                check_response_body(
                    resp, condition=DigaasClient.SERIAL_NOT_LOWER,
                    status="COMPLETED", id=id)
                self.assertGreater(resp.json()['duration'], 0)
                break
            else:
                time.sleep(frequency)

        # Now create a poll_request to check that the zone we just created is
        # removed. This request should timeout because we never deleted the
        # zone through Designate.
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.ZONE_REMOVED,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)

        id = resp.json()['id']

        self.assertEquals(resp.status_code, 202)
        check_response_body(resp, condition=DigaasClient.ZONE_REMOVED, status="ACCEPTED")

        # wait for the request to time out
        time.sleep(timeout + 1)

        resp = self.digaas_client.get_poll_request(id)
        self.assertEquals(resp.status_code, 200)
        check_response_body(resp, condition=DigaasClient.ZONE_REMOVED, status="ERROR", id=id)


if __name__ == '__main__':
    unittest.main()
