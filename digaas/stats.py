import logging
import math

import gevent
from sqlalchemy.sql import select, and_

from digaas.models import DnsQuery
from digaas.models import Observer
from digaas.models import ObserverStats
from digaas.models import Summary
from digaas.models import Plot
from digaas.plot import GnuplotData
from digaas.plot import GnuplotStyle
from digaas.plot import GnuplotConfig
from digaas.plot import GnuplotScript
from digaas.sql import get_engine
from digaas.storage import Storage
from digaas.utils import log_exceptions

LOG = logging.getLogger(__name__)


def fetch_propagation_data(observer_stats):
    """Grab all data within the time range in the ObserverStats object.
    This gives us two views of the data - by observer type and by nameserver.

    The returns a dictionary, data, that looks like:

            data[category][type][status] = [(start_time, duration)]

    - category: either 'by_type' or 'by_nameserver'
    - type:
        - if the category is 'by_type', then type is the observer type
        - if the category is 'by_nameserver', then type is a nameserver ip
    - status: either 'success' or 'error'
    """
    columns = [
        Observer.TABLE.c.start_time,
        Observer.TABLE.c.duration,
        Observer.TABLE.c.type,
        Observer.TABLE.c.status,
        Observer.TABLE.c.nameserver,
    ]

    query = select(columns).where(
        and_(Observer.TABLE.c.start_time >= observer_stats.start,
             Observer.TABLE.c.start_time <= observer_stats.end)
    )
    result = get_engine().execute(query)

    data = {
        'by_type': {},
        'by_nameserver': {},
    }
    for row in result:
        start_time, duration, type, status, nameserver = row
        if type not in data['by_type']:
            data['by_type'][type] = {
                'error': [],
                'success': [],
            }
        if nameserver not in data['by_nameserver']:
            data['by_nameserver'][nameserver] = {
                'error': [],
                'success': [],
            }
        datapoint = (start_time, duration)
        if status == Observer.STATUSES.COMPLETE:
            data['by_type'][type]['success'].append(datapoint)
            data['by_nameserver'][nameserver]['success'].append(datapoint)
        else:
            data['by_type'][type]['error'].append(datapoint)
            data['by_nameserver'][nameserver]['error'].append(datapoint)
    return data


def fetch_dns_query_data(observer_stats):
    """Return all query data in the range given by the observer stats model.

    :returns: data, where data[nameserver][status] = [(timestamp, duration)].
        status is either 'success' or 'error'
    """
    query = select([
        DnsQuery.TABLE.c.nameserver,
        DnsQuery.TABLE.c.status,
        DnsQuery.TABLE.c.timestamp,
        DnsQuery.TABLE.c.duration,
    ]).where(
        and_(DnsQuery.TABLE.c.timestamp >= observer_stats.start,
             DnsQuery.TABLE.c.timestamp <= observer_stats.end)
    )
    rows = get_engine().execute(query)

    data = {}
    for row in rows:
        nameserver, status, timestamp, duration = row
        if nameserver not in data:
            data[nameserver] = {
                'error': [],
                'success': [],
            }
        if status == DnsQuery.STATUSES.SUCCESS:
            data[nameserver]['success'].append((timestamp, duration))
        else:
            data[nameserver]['error'].append((timestamp, duration))
    return data


def _compute_percentile(entries, percentile):
    assert len(entries) > 0
    assert 0 <= percentile <= 100
    index = int(math.ceil((float(percentile) / 100) * (len(entries) - 1)))
    return entries[index][1]


def _compute_average(entries):
    assert len(entries) > 0
    LOG.debug("Computing average for %s points", len(entries))
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
    result['min'] = success[0][1]
    result['max'] = success[-1][1]
    result['median'] = _compute_percentile(success, 50)
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
        for type, entries in data.items()
    }


def compute_query_summary_statistics(data):
    """data is the data returned by fetch_dns_query_data"""
    return {
        nameserver: _compute_summary_stats(entries)
        for nameserver, entries in data.items()
    }


def store_plot(type, gnuplot_script, observer_stats):
    with open(gnuplot_script.get_output_plot_path(), 'rb') as f:
        plot_model = Plot(
            stats_id=observer_stats.id,
            type=type,
            mimetype='image/png',
            image=f.read(),
        )
        Storage.create(plot_model)


def plot_propagation_data_by_type(data, observer_stats):
    COLORS = {
        Observer.TYPES.ZONE_CREATE: "#FF0000",
        Observer.TYPES.ZONE_UPDATE: "#FF7100",
        Observer.TYPES.ZONE_DELETE: "#FFC200",
        Observer.TYPES.RECORD_CREATE: "#0000FF",
        Observer.TYPES.RECORD_UPDATE: "#910DFF",
        Observer.TYPES.RECORD_DELETE: "#0D8CFF",
    }
    # 5 - square
    # 9 - up arrow
    # 11 - down arrow
    POINTTYPES = {
        Observer.TYPES.ZONE_CREATE: 9,
        Observer.TYPES.ZONE_UPDATE: 5,
        Observer.TYPES.ZONE_DELETE: 11,
        Observer.TYPES.RECORD_CREATE: 5,
        Observer.TYPES.RECORD_UPDATE: 5,
        Observer.TYPES.RECORD_DELETE: 5,
    }

    # plot the propagation data by type
    plots = []
    config = GnuplotConfig(
        xlabel="Timestamp of API request",
        ylabel="Propagation time (seconds)",
        title="API-to-nameserver propagation times by change type "
              "(successful propagations only)",
    )
    for type in data['by_type']:
        success_data = data['by_type'][type]['success']
        gnuplot_data = GnuplotData(label=type, points=success_data)
        gnuplot_style = GnuplotStyle(
            pointtype=POINTTYPES.get(type, 5),
            rgb_linecolor=COLORS.get(type),
        )
        plots.append((gnuplot_data, gnuplot_style))
    script = GnuplotScript(config=config, plots=plots)
    script.generate_plot()
    store_plot(Plot.TYPES.PROPAGATION_BY_TYPE, script, observer_stats)


def plot_propagation_data_by_nameserver(data, observer_stats):
    # plot the propagation data by nameserver
    plots = []
    config = GnuplotConfig(
        xlabel="Timestamp of API request",
        ylabel="Propagation time (seconds)",
        title="API-to-nameserver propagation times by nameserver "
              "(successful propagations only)",
    )
    for nameserver in data['by_nameserver']:
        success_data = data['by_nameserver'][nameserver]['success']
        gnuplot_data = GnuplotData(label=nameserver, points=success_data)
        plots.append((gnuplot_data, GnuplotStyle()))
    script = GnuplotScript(config=config, plots=plots)
    script.generate_plot()
    store_plot(Plot.TYPES.PROPAGATION_BY_NAMESERVER, script, observer_stats)


def plot_query_data(data, observer_stats):
    config = GnuplotConfig(
        xlabel="Timestamp of query",
        ylabel="Response time (seconds)",
        title="DNS query response times (successful queries only)",
    )

    plots = []
    for nameserver in data:
        success_data = data[nameserver]['success']
        gnuplot_data = GnuplotData(label=nameserver, points=success_data)
        gnuplot_style = GnuplotStyle()
        plots.append((gnuplot_data, gnuplot_style))
    script = GnuplotScript(config=config, plots=plots)
    script.generate_plot()

    store_plot(Plot.TYPES.QUERY, script, observer_stats)


@log_exceptions(LOG)
def stats_handler(observer_stats):
    propagation_data = fetch_propagation_data(observer_stats)
    if propagation_data:
        # compute observer summaries by type
        propagation_stats = compute_propagation_summary_statistics(
            propagation_data['by_type']
        )
        for type, summary_data in propagation_stats.items():
            LOG.debug("Computed summary %s: %s", type, summary_data)
            d = dict(summary_data)
            d['stats_id'] = observer_stats.id
            d['type'] = type
            d['view'] = Summary.VIEWS.OBSERVERS_BY_TYPE
            Storage.create(Summary(**d))

        # compute observer summaries by nameserver
        propagation_stats = compute_propagation_summary_statistics(
            propagation_data['by_nameserver']
        )
        for nameserver, summary_data in propagation_stats.items():
            LOG.debug("Computed summary %s: %s", type, summary_data)
            d = dict(summary_data)
            d['stats_id'] = observer_stats.id
            d['type'] = nameserver
            d['view'] = Summary.VIEWS.OBSERVERS_BY_NAMESERVER
            Storage.create(Summary(**d))

    plot_propagation_data_by_type(propagation_data, observer_stats)
    plot_propagation_data_by_nameserver(propagation_data, observer_stats)

    # attempt to free up this memory
    del propagation_data

    query_data = fetch_dns_query_data(observer_stats)
    if query_data:
        query_stats = compute_query_summary_statistics(query_data)
        for nameserver, summary_data in query_stats.items():
            LOG.debug("Computed summary %s: %s", nameserver, summary_data)
            d = dict(summary_data)
            d['stats_id'] = observer_stats.id
            d['type'] = nameserver
            d['view'] = Summary.VIEWS.QUERIES
            Storage.create(Summary(**d))
    plot_query_data(query_data, observer_stats)
    del query_data

    observer_stats.status = observer_stats.STATUSES.COMPLETE
    Storage.update(observer_stats)


@log_exceptions(LOG)
def spawn_stats_handler(observer_stats):
    LOG.info("Spawning stats handler %s", observer_stats)
    observer_stats.status = ObserverStats.STATUSES.ACCEPTED
    observer_stats = Storage.create(observer_stats)
    gevent.spawn(stats_handler, observer_stats)
    return observer_stats
