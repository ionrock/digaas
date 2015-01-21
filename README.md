Overview
========
Digaas is "Dig as a Service". It is a simple REST API backed by either sqlite or redis that accepts requests to poll for a zone on a DNS nameserver. Digaas was created to offload this polling functionality to a separate service during a performance test of OpenStack Designate. After the performance test is over, the propagation times for every created/updated/delete zone from Designate's API down the stack to the backend nameserver can be plotted and analyzed.

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

### Implementation overview

Digaas is all Python. It uses falcon for the API and uwsgi in `--gevent` mode for the http server. When a new poll request is made through the API, a new entry is created in the database (marked `ACCEPTED`), a greenlet is spawned (through gevent) to work on the request asyncronously, and a 202 response is returned immediately. The worker greenlet will poll a DNS nameserver until success or until timeout, at which point the relevant status and the duration of that poll request are updated in the database.

Code:

- *app.py* - contains the routing and top-level http request handlers
- *model.py* - contains the PollRequest class which does (de)serialization and validation
- *poll.py* - contains the handler functions that do the actual polling
- *storage_*\*.py* - contains functions for updating the database
- *digaas_config.py* - contains various config options
- *digdig.py* - contains functions that do dns querying
