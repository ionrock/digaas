import logging

import falcon

from digaas.config import cfg
from digaas import resources

CONF = cfg.CONF


class DigaasAPI(falcon.API):

    RESOURCES = [
        resources.RootResource,
        resources.ObserversResource,
        resources.ObserverResource,
        resources.ObserverStatsCollection,
        resources.ObserverStatsResource,
        resources.SummaryResource,
    ]

    def __init__(self, *args, **kwargs):
        super(DigaasAPI, self).__init__(*args, **kwargs)
        for r in self.RESOURCES:
            r().register(self)


def setup_logging():
    FORMAT = \
        '[%(asctime)s] {PID=%(process)d} %(name)s [%(levelname)s] %(message)s'
    logging.basicConfig(
        filename='digaas.log',
        filemode='a',
        format=FORMAT,
        level=logging.DEBUG,
    )


setup_logging()
app = DigaasAPI()
