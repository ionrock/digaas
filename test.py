import json
import random
import unittest
import string
import time
from collections import namedtuple

RecordData = namedtuple('RecordData', ['name', 'data', 'type'])

import requests

from designate_client import DesignateClient

class TimeoutException(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)


class Datagen(object):

    @staticmethod
    def get_random_string(length):
        return "".join(random.choice(string.letters) for _ in xrange(length))

    @staticmethod
    def get_random_ip():
        return ".".join(map(str, [random.randrange(0, 256) for _ in xrange(4)]))

    @classmethod
    def get_random_zone(cls):
        return "{0}.{1}.com.".format(cls.get_random_string(random.randrange(2, 6)),
                                     cls.get_random_string(random.randrange(5, 30)))

    @classmethod
    def get_random_recordset(cls, zone_name):
        host = cls.get_random_string(random.randrange(3, 10))
        return RecordData(
            name="{0}.{1}".format(host, zone_name),
            data=cls.get_random_ip(),
            type="A")

class DigaasClient(object):

    SERIAL_NOT_LOWER = 'serial_not_lower'
    ZONE_REMOVED = 'zone_removed'
    DATA_EQUALS = 'data='

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def _poll_requests_url(self):
        return self.endpoint + '/poll_requests'

    def _poll_request_url(self, id):
        return self._poll_requests_url() + '/' + str(id)

    def post_poll_request(self, query_name, nameserver, serial, condition, start_time,
                          timeout, frequency, rdatatype=None):
        data = dict(
            query_name = query_name,
            nameserver = nameserver,
            serial     = serial,
            condition  = condition,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        if rdatatype is not None:
            data['rdatatype'] = rdatatype

        return requests.post(self._poll_requests_url(),
            data=json.dumps(data))

    def get_poll_request(self, id):
        return requests.get(self._poll_request_url(id))


class TestPollRequest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.digaas_client = DigaasClient(endpoint='http://localhost:9090')
        cls.designate_client = DesignateClient(endpoint='http://162.209.102.65')
        cls.nameserver = '104.130.17.129'

    def post_random_zone(self):
        """Create a random zone through Designate and return the response"""
        zone = Datagen.get_random_zone()
        resp = self.designate_client.post_zone(
            name=zone, email="mickey@example.com", ttl=2400)
        self.assertEquals(resp.status_code, 202)
        return resp

    def post_random_recordset(self, zone_id, zone_name):
        recordset = Datagen.get_random_recordset(zone_name)
        data = {
            "recordset": {
                "name": recordset.name,
                "records": [recordset.data],
                "type": recordset.type,
            }
        }
        resp = self.designate_client.post_recordset(
            zone_id=zone_id,
            data=json.dumps(data))
        self.assertEquals(resp.status_code, 201)
        return resp

    @classmethod
    def wait_for_status(cls, api_call, check, interval, timeout):
        end_time = time.time() + timeout
        while True:
            if time.time() >= end_time:
                raise TimeoutException("Timed out before completion")
            if check(api_call()):
                break
            else:
                time.sleep(interval)

    def test_poll_request_serial_not_lower_timeout(self):
        """Check a poll request times out for an absent zone
        Check that I can:
            1. Submit a poll request with a specific timeout
            2. Wait for the poll request to timeout
            3. See the poll request move to the ERROR state
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
            self.assertEquals(resp.json()['query_name'], zone)
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
            query_name = zone,
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
        """Test that a poll request to time a zone create works.

        Check that I can:
            1. Create a zone
            2. Create a poll request to track the zone to completion
            3. See the poll request move to the COMPLETED state
        """
        # create a random zone
        resp = self.post_random_zone()
        zone = resp.json()['zone']['name']
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']

        start_time = time.time()
        timeout = 60
        frequency = 1

        def check_response_body(resp, status, id=None):
            """Does not check duration"""
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['serial'],     serial)
            self.assertEquals(resp.json()['condition'],  DigaasClient.SERIAL_NOT_LOWER)
            self.assertEquals(resp.json()['query_name'],  zone)
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
            query_name = zone,
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

        api_call = lambda: self.digaas_client.get_poll_request(id)
        def check(resp):
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                check_response_body(resp, status="COMPLETED", id=id)
                self.assertGreater(resp.json()['duration'], 0)
                return True
        self.wait_for_status(api_call, check, frequency, timeout)

    def test_poll_request_zone_removed_completed(self):
        # create the zone
        resp = self.post_random_zone()
        zone = resp.json()['zone']['name']
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']
        timeout = 10
        frequency = 1

        # create the poll request
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            query_name = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.SERIAL_NOT_LOWER,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)

        id = resp.json()['id']

        # poll until we see a COMPLETED
        def check(resp):
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                self.assertGreater(resp.json()['duration'], 0)
                return True
        api_call = lambda: self.digaas_client.get_poll_request(id)
        self.wait_for_status(api_call, check, frequency, timeout)

        # delete the zone
        resp = self.designate_client.delete_zone(zone_id)
        self.assertEquals(resp.status_code, 204)

        # check the zone is removed
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            query_name = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.ZONE_REMOVED,
            start_time = time.time(),
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)

        id = resp.json()['id']

        # poll until we see a "COMPLETED", takes a while with pdns in vagrant
        api_call = lambda: self.digaas_client.get_poll_request(id)
        self.wait_for_status(api_call, check, frequency, timeout)


    def _create_zone_and_wait_for_propagation(self):
        # create the zone
        create_resp = resp = self.post_random_zone()
        zone = resp.json()['zone']['name']
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']
        timeout = 10
        frequency = 1

        def check_response_body(resp, status, condition, id=None):
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['serial'],     serial)
            self.assertEquals(resp.json()['condition'],  condition)
            self.assertEquals(resp.json()['query_name'],  zone)
            self.assertEquals(resp.json()['nameserver'], self.nameserver)
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
            query_name = zone,
            nameserver = self.nameserver,
            serial     = serial,
            condition  = DigaasClient.SERIAL_NOT_LOWER,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)

        id = resp.json()['id']

        # poll until we see a "COMPLETED", so we know the zone is on the nameserver
        api_call = lambda: self.digaas_client.get_poll_request(id)
        def check(resp):
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                check_response_body(
                    resp, condition=DigaasClient.SERIAL_NOT_LOWER,
                    status="COMPLETED", id=id)
                self.assertGreater(resp.json()['duration'], 0)
                return True
        self.wait_for_status(api_call, check, interval=frequency, timeout=timeout)

        return create_resp

    def test_poll_request_zone_removed_timeout(self):
        # create a zone and ensure it's on the nameserver
        resp = self._create_zone_and_wait_for_propagation()
        zone = resp.json()['zone']['name']
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']
        timeout = 3
        frequency = 1

        def check_response_body(resp, status, condition, id=None):
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['serial'],     serial)
            self.assertEquals(resp.json()['condition'],  condition)
            self.assertEquals(resp.json()['query_name'],  zone)
            self.assertEquals(resp.json()['nameserver'], self.nameserver)
            self.assertEquals(resp.json()['frequency'],  frequency)
            self.assertEquals(resp.json()['timeout'],    timeout)
            if id is None:
                self.assertTrue('id' in resp.json())
            else:
                self.assertEquals(resp.json()['id'], id)

        # Now create a poll_request to check that the zone we just created is
        # removed. This request should timeout because we never deleted the
        # zone through Designate.
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            query_name = zone,
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

    def test_poll_request_data_equals_w_record_create_completed(self):
        resp = self._create_zone_and_wait_for_propagation()
        zone = resp.json()['zone']['name']
        zone_id = resp.json()['zone']['id']
        serial = resp.json()['zone']['serial']

        # create a recordset through Designate
        resp = self.post_random_recordset(zone_id, zone)
        record_name = resp.json()["recordset"]["name"]
        record_data = resp.json()["recordset"]["records"][0]
        record_type = resp.json()["recordset"]["type"]
        record_id   = resp.json()["recordset"]["id"]
        timeout = 10
        frequency = 1
        condition  = DigaasClient.DATA_EQUALS + record_data

        def check_response_body(resp, status, condition, id=None):
            self.assertEquals(resp.json()['status'],     status)
            self.assertEquals(resp.json()['start_time'], start_time)
            self.assertEquals(resp.json()['condition'],  condition)
            self.assertEquals(resp.json()['query_name'], record_name)
            self.assertEquals(resp.json()['rdatatype'],  record_type)
            self.assertEquals(resp.json()['nameserver'], self.nameserver)
            self.assertEquals(resp.json()['frequency'],  frequency)
            self.assertEquals(resp.json()['timeout'],    timeout)
            if id is None:
                self.assertTrue('id' in resp.json())
            else:
                self.assertEquals(resp.json()['id'], id)

        # post to digaas with the 'data=' condition to check the record shows up
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            query_name = record_name,
            rdatatype  = record_type,
            nameserver = self.nameserver,
            serial     = 0,
            condition  = condition,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)
        poll_request_id = resp.json()['id']

        # wait for digaas to give us a COMPLETED status
        def check(resp):
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                self.assertGreater(resp.json()['duration'], 0)
                return True
        api_call = lambda: self.digaas_client.get_poll_request(poll_request_id)
        self.wait_for_status(api_call, check, frequency, timeout)

    def _create_recordset_and_wait_for_propagation(self, zone_id, zone):
        # create a recordset through Designate
        create_resp = resp = self.post_random_recordset(zone_id, zone)
        record_name = resp.json()["recordset"]["name"]
        record_data = resp.json()["recordset"]["records"][0]
        record_type = resp.json()["recordset"]["type"]
        record_id   = resp.json()["recordset"]["id"]
        timeout = 10
        frequency = 1

        # post to digaas with the 'data=' condition to check the record shows up
        # we can use digaas to check the record has propagated provided other tests pass
        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            query_name = record_name,
            rdatatype  = record_type,
            nameserver = self.nameserver,
            serial     = 0,
            condition  = DigaasClient.DATA_EQUALS + record_data,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)
        poll_request_id = resp.json()['id']

        # wait for digaas to give us a COMPLETED status
        def check(resp):
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                self.assertGreater(resp.json()['duration'], 0)
                return True
        api_call = lambda: self.digaas_client.get_poll_request(poll_request_id)
        self.wait_for_status(api_call, check, 1, 10)
        return create_resp

    def test_poll_request_zone_removed_w_record_delete_completed(self):
        zone_resp = self._create_zone_and_wait_for_propagation()
        zone_id = zone_resp.json()["zone"]["id"]
        zone_name = zone_resp.json()["zone"]["name"]

        record_resp = self._create_recordset_and_wait_for_propagation(zone_id, zone_name)
        record_name = record_resp.json()["recordset"]["name"]
        record_data = record_resp.json()["recordset"]["records"][0]
        record_type = record_resp.json()["recordset"]["type"]
        recordset_id = record_resp.json()["recordset"]["id"]
        timeout = 10
        frequency = 1

        # tell Designate to delete the recordset
        resp = self.designate_client.delete_recordset(zone_id, recordset_id)
        self.assertEquals(resp.status_code, 204)

        start_time = time.time()
        resp = self.digaas_client.post_poll_request(
            query_name = record_name,
            rdatatype  = record_type,
            nameserver = self.nameserver,
            serial     = 0,
            condition  = DigaasClient.ZONE_REMOVED,
            start_time = start_time,
            timeout    = timeout,
            frequency  = frequency)
        self.assertEquals(resp.status_code, 202)
        poll_request_id = resp.json()['id']

        def check(resp):
            self.assertEquals(resp.status_code, 200)
            if resp.json()['status'] == "COMPLETED":
                self.assertGreater(resp.json()['duration'], 0)
                return True
        api_call = lambda: self.digaas_client.get_poll_request(poll_request_id)
        self.wait_for_status(api_call, check, frequency, timeout)

if __name__ == '__main__':
    unittest.main()
