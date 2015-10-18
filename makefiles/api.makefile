SHELL := /bin/bash

DB_MAKEFILE=$(shell find . -name "db.makefile")
BIND_MAKEFILE=$(shell find . -name "bind.makefile")
BIND_IP=$(shell make -s -f $(BIND_MAKEFILE) ip)
MYSQL_IP=$(shell make -s -f $(DB_MAKEFILE) ip)

help:
	@echo "start            - restart the digaas api"
	@echo "stop             - stop digaas"
	@echo "check            - check the api is running. you should see version info"
	@echo "quickcheck       - restart and check the api (useful to check changes)"
	@echo "config           - write out the api's config file"
	@echo
	@echo "runtests         - run the functional tests"
	@echo "test-config      - write out the test.conf file for the functional tests"
	@echo "                   this needs the database container to be running"

start: stop
	python digaas/api.py &> /dev/null &
	sleep 1

stop:
	pkill -9 python || true

check:
	@curl -s localhost:8123

quickcheck: start
	curl -s localhost:8123 && echo || true
	@pkill -9 python

config:
	@echo -e "[sqlalchemy]\nengine = mysql://root@$(MYSQL_IP)/digaas\n" > digaas.conf
	@echo -e "[graphite]\nhost = \nport = \n" >> digaas.conf
	@echo -e "[digaas]\ndns_query_timeout = 2.0\n" >> digaas.conf
	@echo "-- wrote out digaas.conf --"
	@cat digaas.conf

runtests: test-config start
	specter || true
	@pkill -9 python

test-config:
	@echo -e "[digaas]" > test.conf
	@echo -e "endpoint = http://localhost:8123\n" >> test.conf
	@echo -e "[bind]" >> test.conf
	@echo -e "host = $(BIND_IP)" >> test.conf
	@echo "-- wrote out test.conf --"
	@cat test.conf

