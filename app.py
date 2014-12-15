import json

import falcon

import digdig
import model
import poll
import storage

from pprint import pprint


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


class ResourceCollection(object):
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


class Resource(object):
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

# the uWSGI callable
# Run `uwsgi --wsgi-file thismodule.py --callable app`
app = falcon.API()

resource_collection = ResourceCollection()
resource = Resource()

app.add_route(ResourceCollection.route, resource_collection)
app.add_route(Resource.route, resource)


