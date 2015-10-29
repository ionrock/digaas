import logging
import math

import gevent
from sqlalchemy.sql import select, and_

from digaas.sql import get_engine
from digaas.storage import Storage
from digaas.models import Observer
from digaas.models import ObserverStats
from digaas.models import Summary
from digaas.utils import log_exceptions

LOG = logging.getLogger(__name__)


def fetch_propagation_data(observer_stats):
    """Grab all data within the time range in the ObserverStats object.

    :return: data, such that data[type][status] = [(start_time, duration)]
        where status is either 'error' or 'success' and type is the observer
        type.
    """
    columns = [
        Observer.TABLE.c.start_time,
        Observer.TABLE.c.duration,
        Observer.TABLE.c.type,
        Observer.TABLE.c.status,
    ]

    query = select(columns).where(
        and_(Observer.TABLE.c.start_time >= observer_stats.start,
             Observer.TABLE.c.start_time <= observer_stats.end)
    )
    result = get_engine().execute(query)

    data = {}
    for row in result:
        start_time, duration, type, status = row
        if type not in data:
            data[type] = {
                'error': [],
                'success': [],
            }
        if status == 'COMPLETE':
            data[type]['success'].append((start_time, duration))
        else:
            data[type]['error'].append((start_time, duration))
    return data


def _compute_median(entries):
    assert len(entries) > 0
    mid = int(len(entries) / 2)
    if len(entries) % 2 == 0:
        return float(entries[mid - 1][1] + entries[mid][1]) / 2
    return float(entries[mid][1])


def _compute_percentile(entries, percentile):
    assert len(entries) > 0
    assert 0 <= percentile <= 100
    index = int(math.ceil((float(percentile) / 100) * (len(entries) - 1)))
    return entries[index][1]


def _compute_average(entries):
    assert len(entries) > 0
    LOG.debug("Computing average for %s", entries)
    total = sum(x[1] for x in entries)
    return float(total) / len(entries)


def _compute_summary_stats(entries):
    """A helper for compute_propagation_summary_statistics

    benchmarks on a 2GB cloud server:
        0.026 seconds on 100000 items in entries['success']
        2.234 seconds on 1000000 items in entries['success']
    """
    result = {
        "average": None,
        "median": None,
        "min": None,
        "max": None,
        "per66": None,
        "per75": None,
        "per90": None,
        "per95": None,
        "per99": None,
        "success_count": len(entries['success']),
        "error_count": len(entries['error']),
    }
    # sort by the duration
    success = sorted(entries['success'], key=lambda x: x[1])
    if len(success) == 0:
        return result

    result['average'] = _compute_average(success)
    result['median'] = _compute_median(success)
    result['min'] = success[0][1]
    result['max'] = success[-1][1]
    result['per66'] = _compute_percentile(success, 66)
    result['per75'] = _compute_percentile(success, 75)
    result['per90'] = _compute_percentile(success, 90)
    result['per95'] = _compute_percentile(success, 95)
    result['per99'] = _compute_percentile(success, 99)
    assert result['min'] <= result['median']
    assert result['median'] <= result['per66']
    assert result['per66'] <= result['per75']
    assert result['per75'] <= result['per90']
    assert result['per90'] <= result['per95']
    assert result['per95'] <= result['per99']
    assert result['per99'] <= result['max']
    return result


def compute_propagation_summary_statistics(data):
    """data is the data returned by fetch_propagation_data"""
    return {
        type: _compute_summary_stats(entries)
        for type, entries in data.iteritems()
    }


@log_exceptions(LOG)
def stats_handler(observer_stats):
    data = fetch_propagation_data(observer_stats)
    if not data:
        LOG.debug("No data found for stats id=%s", observer_stats.id)
        observer_stats.status = observer_stats.STATUSES.ERROR
        Storage.update(observer_stats)
        return

    propagation_stats = compute_propagation_summary_statistics(data)
    LOG.debug("propagation_stats: %s", propagation_stats)
    for type, summary_data in propagation_stats.items():
        LOG.debug("Computed summary %s: %s", type, summary_data)
        d = dict(summary_data)
        d['stats_id'] = observer_stats.id
        d['type'] = type
        Storage.create(Summary(**d))
    observer_stats.status = observer_stats.STATUSES.COMPLETE
    Storage.update(observer_stats)


@log_exceptions(LOG)
def spawn_stats_handler(observer_stats):
    LOG.info("Spawning stats handler %s", observer_stats)
    observer_stats.status = ObserverStats.STATUSES.ACCEPTED
    observer_stats = Storage.create(observer_stats)
    gevent.spawn(stats_handler, observer_stats)
    return observer_stats
