import json
import random
import unittest
import string
import time

import requests


class Datagen(object):

    @staticmethod
    def get_random_string(length):
        return "".join(random.choice(string.letters) for _ in xrange(length))

    @classmethod
    def get_random_zone(cls):
        return "{0}.{1}.com.".format(cls.get_random_string(random.randrange(2, 6)),
                                     cls.get_random_string(random.randrange(5, 30)))


class Client(object):

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
        cls.client = Client(endpoint='http://localhost:9090')
        cls.nameserver = '192.168.33.20'

    def _test_poll_request_timeout_w_condition(self, condition):
        """Check that I can:
            1. submit a poll request with the given condition
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
            self.assertEquals(resp.json()['condition'],  condition)
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
        resp = self.client.post_poll_request(
            zone       = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = condition,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)

        # check post response
        self.assertEquals(resp.status_code, 202)
        check_response_body(resp, status="ACCEPTED")

        id = resp.json()['id']

        # get the poll request
        resp = self.client.get_poll_request(id)
        self.assertEquals(resp.status_code, 200)
        check_response_body(resp, status="ACCEPTED", id=id)

        # wait for poll request to timeout
        time.sleep(timeout + frequency)

        resp = self.client.get_poll_request(id)
        self.assertEquals(resp.status_code, 200)
        check_response_body(resp, status="ERROR", id=id)

    def test_poll_request_serial_not_lower_timeout(self):
        self._test_poll_request_timeout_w_condition(Client.SERIAL_NOT_LOWER)

    def test_poll_request_zone_removed_timeout(self):
        self._test_poll_request_timeout_w_condition(Client.SERIAL_NOT_LOWER)

if __name__ == '__main__':
    unittest.main()
