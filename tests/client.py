import json
import requests
import time

class TimeoutException(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)

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

    def _stats_requests_url(self):
        return self.endpoint + '/stats'

    def _stats_request_url(self, id):
        return self._stats_requests_url() + '/' + id

    def get_version(self):
        return requests.get(self.endpoint)

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

    def post_stats_request(self, start, end):
        return requests.post(
            self._stats_requests_url(),
            data=json.dumps({
                'start_time': start,
                'end_time': end,
            }))

    def get_stats_request(self, id):
        return requests.get(self._stats_request_url(id))

    def wait_for_completed_stats_request(self, id):
        api_call = lambda: self.get_stats_request(id)
        def check(resp):
            print resp.text
            assert resp.status_code == 200
            if resp.json()['status'] == "COMPLETED":
                return True
            if resp.json()['status'] in ['ERROR', 'INTERNAL_ERROR']:
                raise Exception('Found %s status while polling for COMPLETED on stats id %s' % (resp.json()['status'], id))
        self.wait_for_status(api_call, check, 1, 30)

    def wait_for_completed_poll_request(self, id):
        api_call = lambda: self.get_poll_request(id)
        def check(resp):
            assert resp.status_code == 200
            if resp.json()['status'] == "COMPLETED":
                return True
            if resp.json()['status'] in ['ERROR', 'INTERNAL_ERROR']:
                raise Exception('Found %s status while polling for COMPLETED on id %s' % (resp.json()['status'], id))
        self.wait_for_status(api_call, check, 1, 30)

    def wait_for_errored_poll_request(self, id):
        api_call = lambda: self.get_poll_request(id)
        def check(resp):
            assert resp.status_code == 200
            if resp.json()['status'] == "ERROR":
                return True
            if resp.json()['status'] in ['COMPLETED', 'INTERNAL_ERROR']:
                raise Exception('Found %s status while waiting for ERROR on id %s' % (resp.json()['status'], id))
        self.wait_for_status(api_call, check, 1, 30)

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
