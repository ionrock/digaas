Digaas
------

Dig as a Service presents an api for querying nameservers. Digaas can:

- Monitor nameservers for propagation of zones/records
- Expose statistics about query response times and propagation times

Digaas was created as a component of performance tests of OpenStack Designate
at Rackspace.

Setup (dev environment)
-----------------------

(This is only tested on Ubuntu 14.04)

The dev environment is a virtualenv + docker containers managed by makefiles.
These instructions will give you:

- mysql running in a docker container
- bind9 running in a docker container
- digaas running in a virtualenv

### Instructions

- [Install docker](https://docs.docker.com/installation/ubuntulinux/). This is know to work with docker version 1.8.3.
- Install some apt dependencies for digaas and the makefiles:

```
apt-get install python-dev python-virtualenv libmysqlclient-dev jq
```

- Create and activate a virtualenv

```
virtualenv .venv
. .ven/bin/activate
```

- Install the pip dependencies inside the virtualenv

```
pip install -r requirements.txt
pip install -r test-requirements.txt
pip install -e .
```

- Run `make start` to build and start the docker containers. The makefile
includes checks to ensure that mysql and bind are running.
- Run `make test` to run the functional tests. This will restart the digaas
api before running the tests, and stop the api afterwards.


API Overview
------------

Digaas exposes two top-level endpoints:

- `/observers` - monitor one nameserver for a single name
- `/stats` - compute statistics and plots about observers and dns queries

### POST /observers

Create an observer to monitor a zone change on a nameserver

##### Request

The observer request json looks like:

```
{
    "name": "example.com.",
    "nameserver": "8.8.8.8",                # must be an ip address
    "start_time": 1469118683,               # a unix timestamp
    "type": "ZONE_CREATE",
    "timeout": 10,                          # in seconds
    "interval": 1,                          # in seconds
    "serial": 1469110000,                   # (ZONE_UPDATE only) the soa serial
}
```

An observer will query the `nameserver` for the `name`. It will query at
`interval` queries per second, for up to `timeout` seconds.

The `type` indicates the success condition, or when the observer should stop
polling. This is one of:

- `ZONE_CREATE`: query until the zone name s found on the nameserver
- `ZONE_UPDATE`: query until the nameserver has a serial greater or equal to
  the observer's serial for the zone
- `ZONE_DELETE`: query until the name is not found on the nameserver

##### Response

The response json looks like:

```
{
    "status": "ACCEPTED",           # ACCEPTED, COMPLETE, ERROR, INTERNAL_ERROR
    "interval": 1,
    "name": "example.com.",
    "start_time": 1469118683,
    "rdatatype": null,              # deprecated
    "timeout": 10,
    "rdata": null,                  # deprecated
    "duration": null,
    "nameserver": "8.8.8.8",
    "type": "ZONE_CREATE",
    "id": 6,
    "serial": null                  # only for ZONE_UPDATE
}
```

This echoes all the fields from the request, along with:

- `id`: the id of the observer
- `duration`: the time, in seconds, it took (since `start_time` until) to
  successfully see the zone operation on the nameserver. This is `null` until
  the observer has a `COMPLETE` status.

*NOTE*: The duration is always computed by subtracting the observer's
`start_time` from timestamp taken locally on a digaas node. It is important to
sync your server's to network time for this reason.

##### Example: Monitor creation of a zone

Request:

```
curl -H 'Content-type: application/json' -H 'Accept: application/json' -X POST -d '{
    "name": "example.com.",
    "nameserver": "8.8.8.8",
    "type": "ZONE_CREATE",
    "interval": 1,
    "start_time": 1469118683,
    "timeout": 10,
    "interval": 1
}' digaas.pglbutt.com/observers
```

This will:

- poll the nameserver `8.8.8.8` for the name `rackspace.com`
- poll at an interval of 1 query per second for up to 10 seconds

Response:

```
{
    "status": "ACCEPTED",
    "interval": 1,
    "name": "example.com.",
    "start_time": 1469118683,
    "rdatatype": null,
    "timeout": 10,
    "rdata": null,
    "duration": null,
    "nameserver": "8.8.8.8",
    "type": "ZONE_CREATE",
    "id": 6,
    "serial": null
}
```

### GET /observers/{id}

Fetch an observer

##### Request

```
curl -H 'Content-type: application/json' -H 'Accept: application/json' digaas.pglbutt.com/observers/6
```

##### Response

```
{
    "status": "COMPLETE",
    "interval": 1,
    "name": "example.com.",
    "start_time": 1469118683,
    "rdatatype": null,
    "timeout": 10,
    "rdata": null,
    "duration": 2180.79,
    "nameserver": "8.8.8.8",
    "type": "ZONE_CREATE",
    "id": 6,
    "serial": null
}
```

This shows a `COMPLETE` status, so the duration is not null. It says that it
took `2180.79` seconds since `start_time` to see the zone `example.com.` live
on the nameserver `8.8.8.8`.

### POST /stats

Create a request to generate statistics

##### Request

```
curl -H 'Content-type: application/json' -H 'Accept: application/json' -X POST -d '{
    "start": 1469100000,
    "end": 1469120000
}' digaas.pglbutt.com/stats
```

This is an asynchronous request to compute statistics and plots. Statistics
will be computed for:

- all observers with `start_time` between the given unix timestamps
- all dns queries made between the given unix timestamps

##### Response

```
{
    "status": "ACCEPTED",
    "start": 0,
    "end": 1469119331,
    "id": 3
}
```

### GET /stats/{id}/summary

Return summary statistics generated by the stats request.

##### Request

```
curl -H 'Content-type: application/json' -H 'Accept: application/json' digaas.pglbutt.com/stats/3/summary
```

##### Response

```
{
  "queries": {
    "8.8.8.8": {
      "per66": 0.0189741,
      "per75": 0.021904,
      "per99": 0.021904,
      "min": 0.0101621,
      "max": 0.021904,
      "average": 0.015467,
      "median": 0.0189741,
      "per90": 0.021904,
      "success_count": 4,
      "error_count": 0,
      "per95": 0.021904
    }
  },
  "observers_by_type": {
    "ZONE_CREATE": {
      "per66": 2180.79,
      "per75": 2180.79,
      "per99": 2180.79,
      "min": 203.477,
      "max": 2180.79,
      "average": 1520.14,
      "median": 2176.16,
      "per90": 2180.79,
      "success_count": 3,
      "error_count": 3,
      "per95": 2180.79
    }
  },
  "observers_by_nameserver": {
    "8.8.8.8": {
      "per66": 2180.79,
      "per75": 2180.79,
      "per99": 2180.79,
      "min": 203.477,
      "max": 2180.79,
      "average": 1520.14,
      "median": 2176.16,
      "per90": 2180.79,
      "success_count": 3,
      "error_count": 3,
      "per95": 2180.79
    }
  },
  "queries_over_threshold": {}
}
```

This includes stats the following fields:

- `observers_by_type`: statistics on observer `duration`s, broken down by
  observer type
- `observers_by_type`: statistics on observer `duration`s, broken down by
  nameserver.
- `queries`: statistics on dns query response times, by nameserver.
- `queries_over_threshold`: statistics on dns query response times
_greater than a specific threshold_, by nameserver (the threshold is specified
in the digaas config file).

*NOTE*: Statistics like min/max/avg and percentiles are generated for
"successful" operations only. Dns queries that timeout and observers without a
`COMPLETE` status are considered "errors".

### GET /stats/{id}/plots/{type}

Fetch plots. These are png images.

There `type` is one of:

- `propagation_by_type`: plots observer durations by type, for "successful"
  (`COMPLETE`) observers
- `propagation_by_nameserver`: plots observer durations by nameserver, for
  "successful" (`COMPLETE`) observers
- `query`: plots dns query response times, for queries that did not timeout

##### Request

All of these requests return a png image.

```
curl digaas.pglbutt.com/stats/1/plots/propagation_by_type -o propagation_by_type.png
curl digaas.pglbutt.com/stats/1/plots/propagation_by_nameserver -o propagation_by_nameserver.png
curl digaas.pglbutt.com/stats/1/plots/query -o query.png
```
