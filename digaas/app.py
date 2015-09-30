import asyncio
import json

import falcon

from digaas.config import cfg
from digaas.models import Observer
from digaas.observe import spawn_observer

CONF = cfg.CONF


VERSION = {
    'service': 'digaas',
    'version': '0.0.2',
}


def make_error_body(msg):
    return json.dumps({'error': msg})

def make_hook_for_model(model_class):
    """Return a hook we can use to deserialize a request to the model

    The deserialized model can be found on req.model
    """
    def hook(req, resp, params):
        params['model'] = None

        body = req.stream.read().decode('utf-8')
        try:
            req_data = json.loads(body)
        except ValueError as e:
            err_msg = '{0}: {1}'.format(str(e), body)
            resp.body = make_error_body(err_msg)
            resp.status = falcon.HTTP_400
            return

        try:
            params['model'] = model_class.from_dict(req_data)
        except Exception as e:
            resp.status = falcon.HTTP_400
            resp.body = make_error_body(str(e))
            return

        try:
            params['model'].validate()
        except ValueError as e:
            err_msg = '{0}: {1}'.format(str(e), body)
            resp.body = make_error_body(err_msg)
            resp.status = falcon.HTTP_400
            params['model'] = None
            return

    return hook


class DigaasResource(object):

    def register(self, app):
        app.add_route(self.ROUTE, self)

class RootResource(DigaasResource):
    ROUTE = '/'

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'application/json'
        resp.body = json.dumps(VERSION)

class ObserversResource(DigaasResource):
    ROUTE = '/observers'

    @falcon.before(make_hook_for_model(Observer))
    def on_post(self, req, resp, model):
        if not model:
            return

        spawn_observer(model)

        resp.content_type = 'application/json'
        resp.body = json.dumps(model.to_dict())
        resp.status = falcon.HTTP_201



class DigaasAPI(falcon.API):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RootResource().register(self)
        ObserversResource().register(self)
        self.add_sink(self.sink, '/')

    def sink(self, req, resp):
        resp.status = falcon.HTTP_404
        resp.body = make_error_body("Not found")


app = DigaasAPI()
