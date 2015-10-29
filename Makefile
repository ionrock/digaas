SHELL := /bin/bash

help:
	@echo "start                - start all the services"
	@echo "stop                 - stop all the services"
	@echo "start-containers     - build and restart the db and bind containers"
	@echo "stop-containers      - kill and remove the containers"
	@echo "start-api            - start digaas"
	@echo "stop-api             - stop digaas"

start-containers: stop-containers
	make -s -f makefiles/db.makefile build
	make -s -f makefiles/db.makefile start
	make -s -f makefiles/bind.makefile build
	make -s -f makefiles/bind.makefile start
	@echo -e "\n-------- waiting for services to start up ---------"
	sleep 10
	@echo -e "\n-------- checking bind is running ---------"
	make -s -f makefiles/bind.makefile check
	@echo -e "\n-------- checking database is running ---------"
	make -s -f makefiles/db.makefile check

stop-containers:
	make -s -f makefiles/db.makefile stop
	make -s -f makefiles/bind.makefile stop

start-api: stop-api
	make -s -f makefiles/api.makefile config
	make -s -f makefiles/api.makefile start
	sleep 0.5
	make -s -f makefiles/api.makefile check

stop-api:
	make -s -f makefiles/api.makefile stop

start: start-api

stop: stop-api

start-all: start-containers start-api

stop-all: stop-api stop-containers

run:
	gunicorn -w 4 --bind '0.0.0.0:8123' digaas.app:app

test: lint
	make -s -f makefiles/api.makefile runtests

lint:
	flake8 --format=pylint digaas/ spec/
