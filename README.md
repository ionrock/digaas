Overview
========
Digaas is "Dig as a Service". It is a tool designed to time the propagation of changes to a DNS nameserver. It does this by polling the nameserver waiting for a particular condition to be satisfied, at which point it stores the time taken to see that request.

Digaas was created to offload this polling functionality to a separate service during a performance test of OpenStack Designate. After the performance test is over, the propagation times for every change from Designate's API to the backend nameserver can be plotted and analyzed.

See documentation at: http://docs.digaas.apiary.io/

### More detail

The workflow looks like:

1. Create a domain/record somewhere (e.g. in OpenStack Designate)
2. Submit a request to Digaas to poll a nameserver for the change you just made
3. (Repeat from the top as many times as you like)
4. Ask Digaas to plot all the changes you just made

Currently, Digaas understands the following changes:

- zone creates or updates by looking for a serial number increase for the zone
- zone deletes by looking for an empty response from the nameserver
- creates or updates of NS and A records by looking for a spcific value in the records data/address/target
- record deletes by looking for an empty response from the nameserver


### Setup

See `scripts/setup.sh` for a setup script.

On Ubuntu:

    sudo apt-get install git python-dev python-pip python-virtualenv ntp gnuplot
    pip install -U pip
    hash -r
    pip install uwsgi Cython falcon gevent dnspython redis

Create `digaas_config.py`. In particular, you'll need to specify the location of your Redis datastore.

    cp digaas_config.py.sample digaas_config.py
    vim digaas_config.py

Important: Because Digaas accepts timestamps generated on other machines, you *need* to synchronize to network time or your plot will look really off.

    sudo apt-get install ntp

To force a synchronization:

    service ntp stop
    ntpd -gq
    service ntp start

Then start the server with:

    bin/digaas.sh

### Example

**Request**: The following is a a request to poll the nameserver `192.168.33.20` for the zone `hello.com.`. The service will dig the nameserver every 1.2 seconds until the nameserver returns a serial number which is not lower than the provided serial in the request (i.e. a serial greater or equal). Otherwise, the request will timeout after 7.3 seconds. The `start_time` is used when computing the time it took for that zone to show up on the nameserver.

    POST /requests
    {
        "nameserver": "192.168.33.20",
        "zone_name": "hello.com.",
        "serial": 1418336470,
        "start_time": 1421867419,
        "timeout": 7.3,
        "frequency": 1.2,
        "condition": "serial_not_lower"
    }

**Response**: The response repeats all of your inputs. The status is one of `ACCEPTED`, `COMPLETED`, or `ERROR`. You can do a `GET /requests/{id}` to check for an updated status. Only if the request has completed will the `duration` be non-null.

    {
        "status": "ACCEPTED",
        "nameserver": "192.168.33.20",
        "zone_name": "hello.com.",
        "start_time": 1421867419,
        "id": "c55986ca-d728-46ae-89ce-545516f29a84",
        "timeout": 7.3,
        "frequency": 1.2,
        "duration": null,
        "serial": 1418336470,
        "condition": "serial_not_lower"
    }

See documentation at: http://docs.digaas.apiary.io/

### Implementation overview

Digaas is all Python. It uses falcon for the API and uwsgi in `--gevent` mode for the http server. When a new poll request is made through the API, a new entry is created in the database (marked `ACCEPTED`), a greenlet is spawned (through gevent) to work on the request asyncronously, and a 202 response is returned immediately. The worker greenlet will poll a DNS nameserver until success or until timeout, at which point the relevant status and the duration of that poll request are updated in the database.

Code:

- *app.py* - contains the routing and top-level http request handlers
- *model.py* - contains the PollRequest class which does (de)serialization and validation
- *poll.py* - contains the handler functions that do the actual polling
- *storage_*\*.py* - contains functions for updating the database
- *digaas_config.py* - contains various config options
- *digdig.py* - contains functions that do dns querying
- *stats.py* - contains code to plot durations over time (using gnuplot)

Right now, `test.py` requires a deployment of OpenStack Designate to effect changes to the nameserver.
