import requests
from spec.common.model import Model


class BaseClient(object):

    def __init__(self, endpoint):
        self.endpoint = endpoint.rstrip('/')

    def _url(self, path):
        return '{0}{1}'.format(self.endpoint, path)

    def get(self, path):
        resp = requests.get(self._url(path))
        resp.model = Model.from_json(resp.text)
        return resp

    def post(self, path, model):
        resp = requests.post(self._url(path), data=model.to_json())
        resp.model = Model.from_json(resp.text)
        return resp

    def delete(self, path):
        return requests.delete(self._url(path))


class DigaasClient(BaseClient):

    def get_root(self):
        return self.get('/')

    def get_observer(self, id):
        return self.get('/observers/{0}'.format(id))

    def post_observer(self, model):
        return self.post('/observers', model)

    def post_stats(self, model):
        return self.post('/stats', model)

    def get_stats(self, id):
        return self.get('/stats/{0}'.format(id))

    def get_summary(self, stats_id):
        return self.get('/stats/{0}/summary'.format(stats_id))
