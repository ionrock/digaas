import json

import falcon

import digdig
import model
import poll
import storage


#import gevent.monkey
#gevent.monkey.patch_socket()

from pprint import pprint


ACCEPTED = "ACCEPTED"
ERROR = "ERROR"
COMPLETED = "COMPLETED"

def make_body(**kwargs):
    return json.dumps(dict(**kwargs))

def make_error_body(message):
    return make_body(message=message)

class ResourceCollection(object):
    @classmethod
    def _parse_json(cls, req, resp):
        """Parse the request. Set resp.stats and resp.body on failure"""
        try:
            body = req.stream.read()
            return json.loads(body)
        except ValueError as e:
            err_msg = str(e) + ': ' + body
            resp.status = falcon.HTTP_400
            resp.body = make_error_body(error_msg)
            return

    def on_post(self, req, resp):
        resp.content_type = 'application/json'
        # parse request
        data = self._parse_json(req, resp)
        if data is None:
            return

        # validate request
        try:
            poll_req = model.PollRequest.from_dict(data)
        except ValueError as e:
            resp.status = falcon.HTTP_400
            resp.body = make_error_body(str(e))
            return

        # handle request
        poll.receive(poll_req)
        resp.status = falcon.HTTP_202
        resp.body = make_body(**poll_req.to_dict())


class Resource(object):
    def on_get(self, req, resp, id):
        try:
            poll_req = storage.get_entry(id)
        except Exception as e:
            resp.status = falcon.HTTP_404  # could be bad request in some cases?
            resp.body = make_error_body(str(e))
            return

        resp.content_type = 'applciation/json'
        resp.status = falcon.HTTP_200
        resp.body = make_body(**poll_req.to_dict())

# the uWSGI callable
# Run `uwsgi --wsgi-file thismodule.py --callable app`
app = falcon.API()

resource_collection = ResourceCollection()
resource = Resource()

app.add_route('/requests', resource_collection)
app.add_route('/requests/{id}', resource)


