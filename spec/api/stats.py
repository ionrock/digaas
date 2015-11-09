import time
from specter import Spec, expect, require

from spec import datagen
from spec.api.observers import BindUtils
from spec.api.observers import ClientUtils
from spec.common.client import DigaasClient
from spec.common.config import cfg
from spec.common.model import Model
from spec.common.rndc import load_rndc_target


CONF = cfg.CONF


class ObserverStats(Spec, BindUtils, ClientUtils):

    def before_all(self):
        self.client = DigaasClient(CONF.digaas.endpoint)
        self.rndc_target = load_rndc_target()

    def can_post_stats(self):
        t = int(time.time())
        model = Model.from_dict({
            'start': t,
            'end': t,
        })
        resp = self.client.post_stats(model)
        require(resp.status_code).to.equal(201)

        expect(resp.model.id).to.be_a(int)
        expect(resp.model.start).to.equal(model.start)
        expect(resp.model.end).to.equal(model.end)
        expect(resp.model.status).to.equal("ACCEPTED")

    def cannot_post_end_before_start(self):
        t = int(time.time())
        model = Model.from_dict({
            'start': t + 1,
            'end': t,
        })
        resp = self.client.post_stats(model)
        require(resp.status_code).to.equal(400)

    def can_get_summary(self):
        start_time = int(time.time())
        self._make_datapoint(start_time, duration_at_least=2)

        model = Model.from_dict({
            'start': start_time,
            'end': start_time,
        })
        resp = self.client.post_stats(model)
        require(resp.status_code).to.equal(201)

        self._wait_for_stats(resp.model.id)
        summary_resp = self.client.get_summary(resp.model.id)
        require(summary_resp.status_code).to.equal(200)

        require(summary_resp.model.observers_by_type).not_to.be_none()
        require(summary_resp.model.observers_by_nameserver).not_to.be_none()
        require(summary_resp.model.queries).not_to.be_none()

        s = summary_resp.model.observers_by_type
        # tests running in parallel may cause some ERRORed observers
        expect(s.ZONE_CREATE.error_count).to.be_a(int)
        expect(s.ZONE_CREATE.success_count).to.be_greater_than(0)

        expect(s.ZONE_CREATE.per66).to.be_a(float)
        expect(s.ZONE_CREATE.per75).to.be_a(float)
        expect(s.ZONE_CREATE.per90).to.be_a(float)
        expect(s.ZONE_CREATE.per95).to.be_a(float)
        expect(s.ZONE_CREATE.per99).to.be_a(float)
        expect(s.ZONE_CREATE.max).to.be_a(float)
        expect(s.ZONE_CREATE.min).to.be_a(float)
        expect(s.ZONE_CREATE.median).to.be_a(float)
        expect(s.ZONE_CREATE.average).to.be_a(float)

        expect(s.ZONE_CREATE.per66).to.be_greater_than(2)
        expect(s.ZONE_CREATE.per75).to.be_greater_than(2)
        expect(s.ZONE_CREATE.per90).to.be_greater_than(2)
        expect(s.ZONE_CREATE.per95).to.be_greater_than(2)
        expect(s.ZONE_CREATE.per99).to.be_greater_than(2)
        expect(s.ZONE_CREATE.max).to.be_greater_than(2)
        expect(s.ZONE_CREATE.min).to.be_greater_than(2)
        expect(s.ZONE_CREATE.median).to.be_greater_than(2)
        expect(s.ZONE_CREATE.average).to.be_greater_than(2)

    def can_get_plots(self):
        start_time = int(time.time())
        self._make_datapoint(start_time, duration_at_least=2)

        model = Model.from_dict({
            'start': start_time,
            'end': start_time,
        })
        resp = self.client.post_stats(model)
        require(resp.status_code).to.equal(201)

        stats_id = resp.model.id
        self._wait_for_stats(stats_id)
        resp = self.client.get_plot(stats_id, 'propagation_by_type')
        expect(resp.status_code).to.equal(200)
        expect(resp.headers['content-type']).to.equal("image/png")

        resp = self.client.get_plot(stats_id, 'propagation_by_nameserver')
        expect(resp.status_code).to.equal(200)
        expect(resp.headers['content-type']).to.equal("image/png")

        resp = self.client.get_plot(stats_id, 'query')
        expect(resp.status_code).to.equal(200)
        expect(resp.headers['content-type']).to.equal("image/png")

    def _wait_for_stats(self, id, timeout=10, interval=1):
        get_resp = None
        end = time.time() + timeout
        while time.time() < end:
            get_resp = self.client.get_stats(id)
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

    def _make_datapoint(self, start_time, duration_at_least):
        zone = datagen.random_zone()
        _, resp = self._post_observer(
            "ZONE_CREATE",
            timeout=duration_at_least + 10,
            start_time=start_time,
            zone=zone
        )
        time.sleep(2)
        self._add_zone_to_bind(zone)
        self._wait_until_complete(resp.model.id)
