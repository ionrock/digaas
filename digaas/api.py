import aiohttp
import asyncio
from aiohttp import web
import json
import functools

from digaas.models import Observer
from digaas.storage import Storage

VERSION = {
    'service': 'digaas',
    'version': '0.0.2',
}

def dump_json(data):
    return json.dumps(data).encode('utf-8')

def parse_json(data):
    return json.loads(data.decode('utf-8'))

async def get_root(request):
    return web.Response(body=dump_json(VERSION))

async def get_observer(request):
    id = request.match_info['id']
    observer = await Storage.get(id, Observer)
    return web.Response(body=dump_json(observer.to_dict()))

async def post_observer(request):
    data = await request.read()
    data = parse_json(data)
    observer = Observer.from_dict(data)
    observer.status = Observer.STATUSES.ACCEPTED

    observer = Storage.create(observer)

    return web.Response(
        body=dump_json(observer.to_dict()),
        status=201,
    )

class API(object):

    ROUTES = {
        ('GET', '/', get_root),
        ('POST', '/observers', post_observer),
        ('GET', '/observers/{id}', get_observer),
    }

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init(loop))
        loop.run_forever()

    async def init(self, loop):
        app = web.Application(loop=loop)
        # app.router.add_route('GET', '/', get_root)
        for route in self.ROUTES:
            app.router.add_route(*route)
        server = await loop.create_server(
            app.make_handler(), self.host, self.port)
        print("digass listening on {0}:{1}".format(self.host, self.port))
        return server


api = API('127.0.0.1', 8123)
api.start()
