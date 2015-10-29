import functools
import json
import logging

import falcon

from digaas import models
from digaas.storage import Storage
from digaas.observe import spawn_observer
from digaas.stats import spawn_stats_handler
from digaas.version import VERSION

LOG = logging.getLogger(__name__)


def make_error_body(msg):
    return json.dumps({'error': msg})


def deserializer(model_class):
    """Return a hook we can use to deserialize a request to the model"""
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


def logged(f):
    @functools.wraps(f)
    def wrapped(self, req, resp, *args, **kwargs):
        LOG.debug("Handling request %s %s", req.method, req.url)
        f(self, req, resp, *args, **kwargs)
        LOG.info("(%s) %s %s", resp.status, req.method, req.url)
    return wrapped


class DigaasResource(object):

    def register(self, app):
        app.add_route(self.ROUTE, self)
        app.add_sink(self.sink, self.ROUTE)

    @logged
    def sink(self, req, resp):
        resp.status = falcon.HTTP_404
        resp.body = make_error_body("Not found")


class RootResource(DigaasResource):
    ROUTE = '/'

    @logged
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'application/json'
        resp.body = json.dumps(VERSION)


class ObserversResource(DigaasResource):
    ROUTE = '/observers'

    @logged
    @falcon.before(deserializer(models.Observer))
    def on_post(self, req, resp, model):
        if not model:
            return

        model = spawn_observer(model)

        resp.content_type = 'application/json'
        resp.body = json.dumps(model.to_dict())
        resp.status = falcon.HTTP_201


class ObserverResource(DigaasResource):
    ROUTE = '/observers/{id}'

    @logged
    def on_get(self, req, resp, id):
        try:
            observer = Storage.get(id, models.Observer)
            resp.content_type = 'application/json'
            resp.body = json.dumps(observer.to_dict())
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.status = falcon.HTTP_404
            resp.body = make_error_body(str(e))


class ObserverStatsCollection(DigaasResource):
    ROUTE = '/stats'

    @logged
    @falcon.before(deserializer(models.ObserverStats))
    def on_post(self, req, resp, model):
        if not model:
            return

        model = spawn_stats_handler(model)

        resp.content_type = 'application/json'
        resp.body = json.dumps(model.to_dict())
        resp.status = falcon.HTTP_201


class ObserverStatsResource(DigaasResource):
    ROUTE = '/stats/{id}'

    @logged
    def on_get(self, req, resp, id):
        try:
            observer_stats = Storage.get(id, models.ObserverStats)
            resp.content_type = 'application/json'
            resp.body = json.dumps(observer_stats.to_dict())
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.status = falcon.HTTP_404
            resp.body = make_error_body(str(e))


class SummaryResource(DigaasResource):
    ROUTE = '/stats/{id}/summary'

    @logged
    def on_get(self, req, resp, id):
        try:
            summaries = Storage.get_summaries(id, models.Summary)
            summaries = models.Summary.view_summaries_as_dict(summaries)
            resp.content_type = 'application/json'
            resp.body = json.dumps(summaries)
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.status = falcon.HTTP_404
            resp.body = make_error_body(str(e))
