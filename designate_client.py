import json
import requests

PROJECT_ID_HEADER = 'X-Auth-Project-ID'
ROLE_HEADER = 'X-Roles'

class DesignateClient(object):
    """Extends a normal client with Designate specific http requests."""

    _HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, endpoint):
        self._endpoint = endpoint.rstrip('/')
        self.client = requests

    def get_url(self, uri):
        return self._endpoint + uri

    @classmethod
    def _prepare_headers(cls, kwargs):
        """Ensures there are Content-Type and Accept headers,
        and that the headers are in the kwargs."""
        new_headers = dict(cls._HEADERS)
        new_headers.update(kwargs.get('headers') or {})
        kwargs['headers'] = new_headers

    #############################################
    # Server calls
    #############################################
    def post_server(self, *args, **kwargs):
        self._prepare_headers(kwargs)
        return self.client.post(self.get_url("/v1/servers"), *args, **kwargs)

    #############################################
    # Quotas calls
    #############################################
    def patch_quotas(self, tenant, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/quotas/{0}".format(tenant))
        return self.client.patch(url, *args, **kwargs)

    #############################################
    # Zone calls
    #############################################
    def get_zone(self, zone_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}".format(zone_id))
        return self.client.get(url, *args, **kwargs)

    def get_zone_by_name(self, zone_name, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones?name={0}".format(zone_name))
        return self.client.get(url, *args, **kwargs)

    def list_zones(self, *args, **kwargs):
        self._prepare_headers(kwargs)
        return self.client.get(self.get_url("/v2/zones"), *args, **kwargs)

    def post_zone(self, name, email, ttl, **kwargs):
        self._prepare_headers(kwargs)
        data = {'zone': {'name': name, 'email': email, 'ttl': ttl}}
        return self.client.post(self.get_url("/v2/zones"),
            data=json.dumps(data), **kwargs)

    def patch_zone(self, zone_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}".format(zone_id))
        return self.client.patch(url, *args, **kwargs)

    def delete_zone(self, zone_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}".format(zone_id))
        return self.client.delete(url, *args, **kwargs)

    def import_zone(self, data, *args, **kwargs):
        """data should be the text from a zone file."""
        kwargs["headers"] = {"Content-Type": "text/dns"}
        self._prepare_headers(kwargs)
        return self.client.post(self.get_url("/v2/zones"), data=data, *args, **kwargs)

    def export_zone(self, zone_id, *args, **kwargs):
        kwargs['headers']['Accept'] = 'text/dns'
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}".format(zone_id))
        return self.client.get(url, *args, **kwargs)

    #############################################
    # Recordset calls
    #############################################
    def list_recordsets(self, zone_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}/recordsets".format(zone_id))
        return self.client.get(url, *args, **kwargs)

    def get_recordset(self, zone_id, recordset_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}/recordsets/{1}".format(zone_id, recordset_id))
        return self.client.get(url, *args, **kwargs)

    def post_recordset(self, zone_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}/recordsets".format(zone_id))
        return self.client.post(url, *args, **kwargs)

    def put_recordset(self, zone_id, recordset_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}/recordsets/{1}".format(zone_id, recordset_id))
        return self.client.put(url, *args, **kwargs)

    def delete_recordset(self, zone_id, recordset_id, *args, **kwargs):
        self._prepare_headers(kwargs)
        url = self.get_url("/v2/zones/{0}/recordsets/{1}".format(zone_id, recordset_id))
        return self.client.delete(url, *args, **kwargs)
