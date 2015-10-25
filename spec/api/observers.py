import time

from specter import Spec, expect, require

from spec import datagen
from spec.common.model import Model
from spec.common.client import DigaasClient
from spec.common.config import cfg
from spec.common.rndc import load_rndc_target

CONF = cfg.CONF


class BindUtils(object):

    def _add_zone_to_bind(self, zone):
        """This will make the zone queryable"""
        _, _, ret = self.rndc_target.write_zone_file(zone)
        require(ret).to.equal(0)

        _, _, ret = self.rndc_target.addzone(zone)
        require(ret).to.equal(0)

    def _update_zone_in_bind(self, updated_zone):
        _, _, ret = self.rndc_target.write_zone_file(updated_zone)
        require(ret).to.equal(0)

        _, _, ret = self.rndc_target.reload(updated_zone)
        require(ret).to.equal(0)

    def _remove_zone_from_bind(self, zone):
        """Remove the zone and zone file from bind"""
        _, _, ret = self.rndc_target.delzone(zone)
        require(ret).to.equal(0)

        _, _, ret = self.rndc_target.delete_zone_file(zone)
        require(ret).to.equal(0)


class ClientUtils(object):

    def _post_observer(self, type, timeout=5):
        """Returns a tuple (observer, resp) where observer is the model that
        was posted to the api. The returned model is resp.model"""
        observer = Model.from_dict({
            "name": self.zone.name,
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": timeout,
            "type": type,
        })
        resp = self.client.post_observer(observer)
        require(resp.status_code).to.equal(201)
        return observer, resp

    def _post_zone_update_observer(self, updated_zone, timeout=5):
        observer = Model.from_dict({
            "name": updated_zone.name,
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": timeout,
            "type": "ZONE_UPDATE",
            "serial": updated_zone.serial,
        })
        resp = self.client.post_observer(observer)
        require(resp.status_code).to.equal(201)
        return observer, resp

    def _post_record_observer(self, type, record, timeout=5):
        observer = Model.from_dict({
            "name": record.name,
            "nameserver": CONF.bind.host,
            "start_time": int(time.time()),
            "interval": 1,
            "timeout": timeout,
            "type": type,
            "rdata": record.data,
            "rdatatype": record.type,
        })
        resp = self.client.post_observer(observer)
        require(resp.status_code).to.equal(201)
        return observer, resp

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


class ZoneObservers(Spec, BindUtils, ClientUtils):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)
        self.rndc_target = load_rndc_target()

    def before_each(self):
        self.zone = datagen.random_zone()

    def can_post_zone_create_observer(self):
        observer, resp = self._post_observer(type="ZONE_CREATE")

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
        _, post_resp = self._post_observer(type="ZONE_CREATE")

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
        _, resp = self._post_observer(type="ZONE_CREATE", timeout=2)
        time.sleep(3)
        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def zone_create_observer_goes_to_active_on_created_zone(self):
        _, resp = self._post_observer(type="ZONE_CREATE", timeout=10)
        time.sleep(2)
        self._add_zone_to_bind(self.zone)

        get_resp = self._wait_until_complete(resp.model.id, timeout=2)
        require(get_resp).not_to.be_none()
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_a(int)
        expect(get_resp.model.duration).to.be_greater_than(2)

    def zone_delete_observer_goes_to_error_on_timeout(self):
        self._add_zone_to_bind(self.zone)
        _, resp = self._post_observer(type="ZONE_DELETE", timeout=2)
        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def zone_delete_observer_goes_to_active_on_deleted_zone(self):
        self._add_zone_to_bind(self.zone)
        _, resp = self._post_observer(type="ZONE_DELETE", timeout=10)
        time.sleep(2)
        self._remove_zone_from_bind(self.zone)

        get_resp = self._wait_until_complete(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_greater_than(2)

    def zone_update_observer_goes_to_error_on_absent_zone(self):
        _, resp = self._post_zone_update_observer(self.zone, timeout=2)
        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")

    def zone_update_observer_goes_to_error_on_non_updated_zone(self):
        updated_zone = self.zone.clone()
        updated_zone.serial += 1

        self._add_zone_to_bind(self.zone)
        _, resp = self._post_zone_update_observer(updated_zone, timeout=2)
        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")

    def zone_update_observer_goes_to_active_on_updated_serial(self):
        updated_zone = self.zone.clone()
        updated_zone.serial += 1

        self._add_zone_to_bind(self.zone)
        _, resp = self._post_zone_update_observer(updated_zone, timeout=10)
        time.sleep(2)
        self._update_zone_in_bind(updated_zone)

        get_resp = self._wait_until_complete(resp.model.id)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_greater_than(2)


class RecordObservers(Spec, BindUtils, ClientUtils):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)
        self.rndc_target = load_rndc_target()

    def before_each(self):
        self.zone = datagen.random_zone()
        self.record = datagen.random_record(self.zone)
        self.updated_record = self.record.clone()
        self.updated_record.data = datagen.random_ip()

    def record_create_observer_goes_to_error_on_absent_zone(self):
        _, resp = self._post_record_observer(
            type="RECORD_CREATE", record=self.record, timeout=2)
        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def record_update_observer_goes_to_error_on_absent_zone(self):
        _, resp = self._post_record_observer(
            type="RECORD_UPDATE", record=self.record, timeout=2)
        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def record_create_observer_goes_to_active_on_created_record(self):
        self._add_zone_to_bind(self.zone)
        _, resp = self._post_record_observer(
            type="RECORD_CREATE", record=self.record, timeout=10)
        time.sleep(2)

        # create the record in bind. be sure to bump the serial or maybe bind
        # won't see the update (maybe that's only for slaves pulling changes)
        updated_zone = self.zone.clone()
        updated_zone.records.add(self.record)
        updated_zone.serial += 1

        self._update_zone_in_bind(updated_zone)
        get_resp = self._wait_until_complete(resp.model.id)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_greater_than(2)

    def record_update_observer_goes_to_error_on_non_updated_record(self):
        # push out a record
        self.zone.records.add(self.record)
        self._add_zone_to_bind(self.zone)

        # watch for a different record
        _, resp = self._post_record_observer(
            type="RECORD_UPDATE", record=self.updated_record, timeout=2)

        # ensure we timeout
        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def record_update_observer_goes_to_active_on_updated_record(self):
        # push out the initial record
        initial_zone = self.zone.clone()
        initial_zone.records.add(self.record)
        self._add_zone_to_bind(initial_zone)

        # watch for the updated record
        _, resp = self._post_record_observer(
            type="RECORD_UPDATE", record=self.updated_record, timeout=10)
        time.sleep(2)

        # push out the updated record
        updated_zone = self.zone.clone()
        updated_zone.records.add(self.updated_record)
        updated_zone.serial += 1
        self._update_zone_in_bind(updated_zone)

        # check digaas found the updated record
        get_resp = self._wait_until_complete(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_greater_than(2)

    def record_delete_observer_goes_to_error_on_never_deleted_record(self):
        self.zone.records.add(self.record)
        self._add_zone_to_bind(self.zone)

        _, resp = self._post_record_observer(
            type="RECORD_DELETE", record=self.record, timeout=2)

        time.sleep(3)

        get_resp = self.client.get_observer(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("ERROR")
        expect(get_resp.model.duration).to.be_none()

    def record_delete_observer_goes_to_active_on_deleted_record(self):
        self.zone.records.add(self.record)
        self._add_zone_to_bind(self.zone)

        _, resp = self._post_record_observer(
            type="RECORD_DELETE", record=self.record, timeout=10)
        time.sleep(2)

        # remove the record, but don't remove the zone
        self.zone.records.remove(self.record)
        self.zone.serial += 1
        self._update_zone_in_bind(self.zone)

        get_resp = self._wait_until_complete(resp.model.id)
        require(get_resp.status_code).to.equal(200)
        expect(get_resp.model.status).to.equal("COMPLETE")
        expect(get_resp.model.duration).to.be_greater_than(2)
