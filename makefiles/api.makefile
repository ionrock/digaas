SHELL := /bin/bash

DB_MAKEFILE=$(shell find . -name "db.makefile")
BIND_MAKEFILE=$(shell find . -name "bind.makefile")
GRAPHITE_MAKEFILE=$(shell find . -name "graphite.makefile")

BIND_IP=$(shell make -s -f $(BIND_MAKEFILE) ip)
MYSQL_IP=$(shell make -s -f $(DB_MAKEFILE) ip)
GRAPHITE_IP=$(shell make -s -f $(GRAPHITE_MAKEFILE) ip)

DIGAAS_CONF=digaas.conf
TEST_CONF=test.conf

help:
	@echo "start            - restart the digaas api"
	@echo "stop             - stop digaas"
	@echo "check            - check the api is running. you should see version info"
	@echo "config           - write out the api's config file ($(DIGAAS_CONF))"
	@echo
	@echo "runtests         - run the functional tests"
	@echo "test-config      - write config file for the tests ($(TEST_CONF))"

start: stop
	gunicorn --daemon -w 4 --bind '127.0.0.1:8123' digaas.app:app
	sleep 1

stop:
	pkill -9 gunicorn || true

check:
	@curl -s localhost:8123

config:
	@rm -f $(DIGAAS_CONF) && touch $(DIGAAS_CONF)
	@echo -e "[sqlalchemy]"                               >> $(DIGAAS_CONF)
	@echo -e "engine = mysql://root@$(MYSQL_IP)/digaas\n" >> $(DIGAAS_CONF)
	@echo -e "[graphite]"                                 >> $(DIGAAS_CONF)
	@echo -e "host = $(GRAPHITE_IP)"                      >> $(DIGAAS_CONF)
	@echo -e "port = 2023\n"                              >> $(DIGAAS_CONF)
	@echo -e "[digaas]"                                   >> $(DIGAAS_CONF)
	@echo -e "dns_query_timeout = 2.0"                    >> $(DIGAAS_CONF)
	@echo -e "tmp_dir = /tmp/digaas"                      >> $(DIGAAS_CONF)

runtests: test-config start
	specter --parallel --num-processes 8 || true
	@pkill -9 gunicorn

test-config:
	@rm -f $(TEST_CONF) && touch $(TEST_CONF)
	@echo -e "[digaas]"                           >> $(TEST_CONF)
	@echo -e "endpoint = http://localhost:8123\n" >> $(TEST_CONF)
	@echo -e "[bind]"                             >> $(TEST_CONF)
	@echo -e "host = $(BIND_IP)"                  >> $(TEST_CONF)
	@echo -e "type = docker\n"                    >> $(TEST_CONF)
	@echo -e "[bind:docker]"                      >> $(TEST_CONF)
	@echo -e "dir = /var/cache/bind"              >> $(TEST_CONF)
	@echo -e "id = digaas-bind"                   >> $(TEST_CONF)
