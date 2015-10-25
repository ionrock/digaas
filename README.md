Digaas
------

Dig as a Service presents an api for querying nameservers. Digaas can:

- Query multiple nameservers for a name
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

- (Install docker)[https://docs.docker.com/installation/ubuntulinux/]. You
should have docker version 1.8.3+ installed.
- Install some apt dependencies for digaas and the makefiles:

```
apt-get install python-dev python-virtualenv libmysqlclient-dev jq
```

- Create and activate a virtualenv

```
virtualenv .venv
. .ven/bin/activate

- Install the pip dependencies inside the virtualenv

```
pip install -r requirements.txt
pip install -r test-requirements.txt
pip install -e .
```

- Run `make start` to build and start the docker containers. The makefile
includes checks to ensure that mysql and bind are running.
- Run `make test` to run the funtional tests. This will restart the digaas api
before running the tests, and stop the api afterwards.
