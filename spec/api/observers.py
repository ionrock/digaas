import time

from specter import Spec, expect

from spec.common.model import Model
from spec.common.client import DigaasClient
from spec.common.config import cfg

CONF = cfg.CONF


class Observers(Spec):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)

    def can_get_root(self):
        resp = self.client.get_root()
        expect(resp.status_code).to.equal(200)
        expect(resp.model.service).to.equal("digaas")
        expect(resp.model.version).to.equal("0.0.2")

    def can_post_zone_create_observer(self):
        model = Model.from_dict({
            "name": "hello.com.",
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": 10,
            "type": "ZONE_CREATE",
        })
        resp = self.client.post_observer(model)

        expect(resp.model.name).to.equal(model.name)
        expect(resp.model.nameserver).to.equal(model.nameserver)
        expect(resp.model.start_time).to.equal(model.start_time)
        expect(resp.model.interval).to.equal(model.interval)
        expect(resp.model.timeout).to.equal(model.timeout)
        expect(resp.model.type).to.equal(model.type)
