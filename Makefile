SHELL := /bin/bash

BIND_TAG=digaas-bind
MYSQL_TAG=digaas-mysql

BIND_CID=$(shell docker ps | grep $(BIND_TAG) | cut -f1 -d' ')
MYSQL_CID=$(shell docker ps | grep $(MYSQL_TAG) | cut -f1 -d' ')
BIND_IP=$(shell docker inspect $(BIND_CID) | jq -r '.[0].NetworkSettings.IPAddress')
MYSQL_IP=$(shell docker inspect $(MYSQL_CID) | jq -r '.[0].NetworkSettings.IPAddress')


start-uwsgi: stop-uwsgi
	uwsgi --master --die-on-term --emperor /tmp --http :8123 --wsgi-file digaas/app.py --callable app --log-syslog &
	@sleep 1

stop-uwsgi:
	@pkill -9 uwsgi || true

check-digaas:
	@curl -s localhost:8123

quickcheck: start-uwsgi
	curl -s localhost:8123 && echo || true
	@pkill uwsgi

runtests: start-uwsgi
	specter
	@pkill uwsgi

test-config:
	@echo -e "[digaas]\nendpoint = localhost:8123\n\n[bind]\nhost = $(BIND_IP)" > test.conf
	cat test.conf

digaas-config:
	@echo -e "[sqlalchemy]\nengine = mysql://root@$(MYSQL_IP)/digaas\n" > digaas.conf
	@echo -e "[graphite]\nhost = \nport = \n" >> digaas.conf
	@echo -e "[digaas]\ndns_query_timeout = 2.0\n" >> digaas.conf
	cat digaas.conf


########################################
# Docker stuff
########################################
build: build-bind build-mysql

start: start-bind start-mysql

stop: stop-bind stop-mysql

check: check-bind check-mysql

clean: stop
	docker rmi -f $(BIND_TAG) || true

ips:
	@echo "Bind: $(BIND_IP)"
	@echo "Mysql: $(MYSQL_IP)"


########################################
# Bind docker
########################################
build-bind:
	cd dockerfiles && docker build -t $(BIND_TAG) -f ./Dockerfile.bind .

start-bind:
	docker run --name $(BIND_TAG) -d -t $(BIND_TAG)

check-bind:
	rndc -k dockerfiles/rndc.key -s $(BIND_IP) status

stop-bind:
	docker kill $(BIND_TAG) || true
	docker rm -f $(BIND_TAG) || true

bind-ip:
	@echo $(BIND_IP)


########################################
# database docker
########################################
build-mysql:
	cd dockerfiles && docker build -t $(MYSQL_TAG) -f ./Dockerfile.mysql .

start-mysql:
	@docker run --name $(MYSQL_TAG) -d -t $(MYSQL_TAG)

check-mysql:
	mysql -h $(MYSQL_IP) -u root -e status

stop-mysql:
	docker kill $(MYSQL_TAG) || true
	docker rm -f $(MYSQL_TAG) || true

mysql-ip:
	@echo $(MYSQL_IP)

sql-engine:
	@echo "mysql://root@$(MYSQL_IP)/digaas"

mysql-shell:
	mysql -h $(MYSQL_IP) -u root
