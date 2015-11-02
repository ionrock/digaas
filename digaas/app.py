import logging

import falcon

from digaas import graphite
from digaas import resources
from digaas import utils
from digaas.config import cfg

CONF = cfg.CONF


class DigaasAPI(falcon.API):

    RESOURCES = [
        resources.RootResource,
        resources.ObserversResource,
        resources.ObserverResource,
        resources.ObserverStatsCollection,
        resources.ObserverStatsResource,
        resources.SummaryResource,
        resources.PlotResource,
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


def setup_tmp_dir():
    utils.ensure_dir_exists(CONF.digaas.tmp_dir)


def setup_graphite():
    graphite.setup(CONF.graphite.host, CONF.graphite.port)


setup_tmp_dir()
setup_logging()
setup_graphite()
app = DigaasAPI()
