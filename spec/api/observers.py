import time

from specter import Spec, expect, require

from spec.common.model import Model
from spec.common.client import DigaasClient
from spec.common.config import cfg

CONF = cfg.CONF


class Version(Spec):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)

    def getting_root_returns_the_version(self):
        resp = self.client.get_root()
        expect(resp.status_code).to.equal(200)
        expect(resp.model.service).to.equal("digaas")
        expect(resp.model.version).to.equal("0.0.2")


class Observers(Spec):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)

    def _post_observer(self, timeout=5):
        observer = Model.from_dict({
            "name": "hello.com.",
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": timeout,
            "type": "ZONE_CREATE",
        })
        resp = self.client.post_observer(observer)
        require(resp.status_code).to.equal(201)
        return observer, resp

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

        expect(post_resp.model.name).to.equal(get_resp.model.name)
        expect(post_resp.model.nameserver).to.equal(get_resp.model.nameserver)
        expect(post_resp.model.start_time).to.equal(get_resp.model.start_time)
        expect(post_resp.model.interval).to.equal(get_resp.model.interval)
        expect(post_resp.model.timeout).to.equal(get_resp.model.timeout)
        expect(post_resp.model.type).to.equal(get_resp.model.type)

        expect(type(post_resp.model.id)).to.equal(type(get_resp.model.id))
        expect(post_resp.model.id).to.equal(get_resp.model.id)
        expect(post_resp.model.status).to.be_in(["ACCEPTED", "COMPLETE"])
        expect(post_resp.model.duration).to.equal(get_resp.model.duration)
        expect(post_resp.model.serial).to.equal(get_resp.model.serial)
        expect(post_resp.model.rdata).to.equal(get_resp.model.rdata)
        expect(post_resp.model.rdatatype).to.equal(get_resp.model.rdatatype)

    def zone_create_observer_goes_to_error_on_timeout(self):
        observer, resp = self._post_observer(timeout=3)
        time.sleep(3)
        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()
