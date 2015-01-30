"""
The main module for the digaas service. This contains routing and top-level
request handlers. To start the service on port 9090, run with uwsgi:

    uwsgi --http :9090 --gevent <cores> --wsgi-file <this_module> --callable app

Where
    <cores> is the number of cores (threads) to use?
    <this_module> is this python module, e.g. "app.py"
    the callable is a variable in this file that knows how to handle requests:
        app = falcon.API()
"""
import json
import os

import falcon

import digdig
import model
import poll
import stats
from digaas_config import storage


def make_error_body(message):
    return json.dumps(dict(message=message))

def _parse_json(req, resp):
    """Parse the request. Set resp.status and resp.body on failure
    :param req: a falcon request object
    :param resp: a falcon response object
    """
    try:
        body = req.stream.read()
        return json.loads(body)
    except ValueError as e:
        err_msg = str(e) + ': ' + body
        resp.status = falcon.HTTP_400
        resp.body = make_error_body(err_msg)
        return


class PollRequestCollection(object):
    route = '/requests'

    def on_post(self, req, resp):
        """Handle POST /requests"""
        resp.content_type = 'application/json'
        # parse request
        data = _parse_json(req, resp)
        if data is None:
            return

        # validate request
        try:
            model.PollRequest.validate(data)
        except ValueError as e:
            resp.status = falcon.HTTP_400
            resp.body = make_error_body(str(e))
            return

        try:
            poll_req = model.PollRequest.from_dict(data)
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.body = make_error_body(str(e))
            return

        # handle request
        poll.receive(poll_req)
        resp.status = falcon.HTTP_202
        resp.body = json.dumps(poll_req.to_dict())


class PollRequestResource(object):
    route = "/requests/{id}"

    def on_get(self, req, resp, id):
        """Handle GET /requests/{id}"""
        resp.content_type = 'application/json'
        try:
            poll_req = storage.get_poll_request(id)
            if poll_req is None:
                raise Exception("Poll request id {0} not found".format(id))
        except Exception as e:
            resp.status = falcon.HTTP_404  # could be bad request in some cases?
            resp.body = make_error_body(str(e))
            return

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(poll_req.to_dict())


class StatsCollection(object):
    route = '/stats'

    def on_post(self, req, resp):
        resp.content_type = 'application/json'

        data = _parse_json(req, resp)
        if data is None:
            return

        try:
            model.StatsRequest.validate(data)
        except ValueError as e:
            resp.status = falcon.HTTP_400
            resp.body = make_error_body(str(e))
            return

        try:
            stats_req = model.StatsRequest.from_dict(data)
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.body = make_error_body(str(e))
            return

        stats.receive(stats_req)
        resp.status = falcon.HTTP_202
        resp.body = json.dumps(stats_req.to_dict())


class StatsResource(object):
    route = '/stats/{id}'

    def on_get(self, req, resp, id):
        """Handle GET /stats/{id}"""
        resp.content_type = 'application/json'
        try:
            stats_req = storage.get_stats_request(id)
            if stats_req is None:
                raise Exception("Stats request id {0} not found".format(id))
        except Exception as e:
            print e
            resp.status = falcon.HTTP_404  # could be bad request in some cases?
            resp.body = make_error_body(str(e))
            return

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(stats_req.to_dict())


class ImageResource(object):
    route = '/images/{id}'

    def _get_mime_type(self, filename):
        if filename is None:
            return None

        # note: chrome will display a .jpg with either image/png or image/jpeg
        #       but it will fail if given image/svg+xml or image/tiff.
        if filename.endswith('.png'):
            return 'image/png'
        elif filename.endswith('.svg'):
            return 'image/svg+xml'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return 'image/jpeg'

    def on_get(self, req, resp, id):
        """Handle GET /images/{id}"""

        filename = storage.get_image_filename(id)

        if filename is None:
            resp.status = falcon.HTTP_404
            return
        elif not os.path.exists(filename):
            resp.status = falcon.HTTP_500
            return

        resp.content_type = self._get_mime_type(filename) or 'image/jpeg'

        try:
            with open(filename) as f:
                resp.body = f.read()
            resp.status = HTTP_200
        except:
            resp.status = falcon.HTTP_500


# the uWSGI callable
app = falcon.API()

def add_resource(class_name):
    resource = class_name()
    app.add_route(resource.route, resource)

add_resource(PollRequestCollection)
add_resource(PollRequestResource)
add_resource(StatsCollection)
add_resource(StatsResource)
add_resource(ImageResource)
