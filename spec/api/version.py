from specter import Spec, expect

from spec.common.client import DigaasClient
from spec.common.config import cfg


class Version(Spec):

    def before_all(self):
        self.client = DigaasClient(cfg.CONF.digaas.endpoint)

    def getting_root_returns_the_version(self):
        resp = self.client.get_root()
        expect(resp.status_code).to.equal(200)
        expect(resp.model.service).to.equal("digaas")
        expect(resp.model.version).to.equal("0.0.2")
