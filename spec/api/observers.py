import time

from specter import Spec, expect, require

from spec.common.model import Model
from spec.common.client import DigaasClient
from spec.common.config import cfg

CONF = cfg.CONF


class Observers(Spec):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)

    def _post_observer(self):
        observer = Model.from_dict({
            "name": "hello.com.",
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": 10,
            "type": "ZONE_CREATE",
        })
        resp = self.client.post_observer(observer)
        require(resp.status_code).to.equal(201)
        return observer, resp

    def can_get_root(self):
        resp = self.client.get_root()
        expect(resp.status_code).to.equal(200)
        expect(resp.model.service).to.equal("digaas")
        expect(resp.model.version).to.equal("0.0.2")

    def can_post_zone_create_observer(self):
        observer, resp = self._post_observer()

        expect(resp.model.name).to.equal(observer.name)
        expect(resp.model.nameserver).to.equal(observer.nameserver)
        expect(resp.model.start_time).to.equal(observer.start_time)
        expect(resp.model.interval).to.equal(observer.interval)
        expect(resp.model.timeout).to.equal(observer.timeout)
        expect(resp.model.type).to.equal(observer.type)
        expect(resp.model.id).to.be_a(int)
        expect(resp.model.status).to.equal("ACCEPTED")
        expect(resp.model.duration).to.be_none()
        expect(resp.model.serial).to.be_none()
        expect(resp.model.rdata).to.be_none()
        expect(resp.model.rdatatype).to.be_none()

    def can_get_zone_create_observer(self):
        _, post_resp = self._post_observer()

        get_resp = self.client.get_observer(post_resp.model.id)
        require(get_resp.status_code).to.equal(200)
        observer = get_resp.model

        expect(post_resp.model.name).to.equal(observer.name)
        expect(post_resp.model.nameserver).to.equal(observer.nameserver)
        expect(post_resp.model.start_time).to.equal(observer.start_time)
        expect(post_resp.model.interval).to.equal(observer.interval)
        expect(post_resp.model.timeout).to.equal(observer.timeout)
        expect(post_resp.model.type).to.equal(observer.type)

        expect(type(post_resp.model.id)).to.equal(type(observer.id))
        expect(post_resp.model.id).to.equal(observer.id)
        expect(post_resp.model.status).to.be_in(["ACCEPTED", "COMPLETE"])
        expect(post_resp.model.duration).to.equal(observer.duration)
        expect(post_resp.model.serial).to.equal(observer.serial)
        expect(post_resp.model.rdata).to.equal(observer.rdata)
        expect(post_resp.model.rdatatype).to.equal(observer.rdatatype)


