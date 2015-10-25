import time

from specter import Spec, expect, require

from spec import datagen
from spec.common.model import Model
from spec.common.client import DigaasClient
from spec.common.config import cfg
from spec.common.rndc import load_rndc_target

CONF = cfg.CONF


class Observers(Spec):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)
        self.rndc_target = load_rndc_target()

    def before_each(self):
        self.zone = datagen.random_zone()

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
        observer, resp = self._post_observer(timeout=2)
        time.sleep(3)
        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def zone_create_observer_goes_to_active_on_created_zone(self):
        _, resp = self._post_observer(timeout=10)
        time.sleep(2)
        self._add_zone_to_bind(self.zone)

        get_resp = self._wait_until_complete(resp.model.id, timeout=2)
        require(get_resp).not_to.be_none()
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_a(int)
        expect(get_resp.model.duration).to.be_greater_than(2)

    def _post_observer(self, timeout=5):
        observer = Model.from_dict({
            "name": self.zone.name,
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": timeout,
            "type": "ZONE_CREATE",
        })
        resp = self.client.post_observer(observer)
        require(resp.status_code).to.equal(201)
        return observer, resp

    def _add_zone_to_bind(self, zone):
        """This will make the zone queryable"""
        _, _, write_zone_file_ret = self.rndc_target.write_zone_file(zone)
        require(write_zone_file_ret).to.equal(0)

        _, _, addzone_ret = self.rndc_target.addzone(zone)
        require(addzone_ret).to.equal(0)

    def _remove_zone_from_bind(self, zone):
        """Remove the zone and zone file from bind"""
        _, _, delzone_ret = self.rndc_target.delzone(zone)
        require(delzone_ret).to.equal(0)

        _, _, delete_zone_file_ret = self.rndc_target.delete_zone_file(zone)
        require(delete_zone_file_ret).to.equal(0)

    def _wait_until_complete(self, id, timeout=10, interval=0.5):
        get_resp = None
        end = time.time() + timeout
        while time.time() < end:
            get_resp = self.client.get_observer(id)
            require(get_resp.status_code).to.equal(200)
            if get_resp.model.status == "COMPLETE":
                return get_resp
            elif get_resp.model.status == "ERROR":
                raise Exception("Observer %s went to error" % get_resp.model)
            time.sleep(interval)
        msg = "Timed out waiting for a COMPLETE status"
        if get_resp:
            msg += ": %s" % get_resp.model
        raise Exception(msg)
