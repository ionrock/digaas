import json
import logging

FORMAT='[%(asctime)s] {PID=%(process)d} %(name)s [%(levelname)s] %(message)s'
logging.basicConfig(
    filename='digaas.log',
    filemode='a',
    format=FORMAT,
    level=logging.DEBUG,
)

from gevent.monkey import patch_all
patch_all()
import falcon

from digaas.config import cfg
from digaas import resources

CONF = cfg.CONF


class DigaasAPI(falcon.API):

    RESOURCES = [
        resources.RootResource,
        resources.ObserversResource,
        resources.ObserverResource,
    ]

    def __init__(self, *args, **kwargs):
        super(DigaasAPI, self).__init__(*args, **kwargs)
        for r in self.RESOURCES:
            r().register(self)

app = DigaasAPI()
