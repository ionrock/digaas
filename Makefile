SHELL := /bin/bash

help:
	@echo "start                - start all the services"
	@echo "stop                 - stop all the services"
	@echo "start-containers     - build and restart the db and bind containers"
	@echo "stop-containers      - kill and remove the containers"
	@echo "start-api            - start digaas"
	@echo "stop-api             - stop digaas"

start-containers: stop-containers
	make -f makefiles/db.makefile build
	make -f makefiles/db.makefile start
	make -f makefiles/bind.makefile build
	make -f makefiles/bind.makefile start
	@echo -e "\n-------- waiting for services to start up ---------"
	sleep 10
	@echo -e "\n-------- checking bind is running ---------"
	make -f makefiles/bind.makefile check
	@echo -e "\n-------- checking database is running ---------"
	make -f makefiles/db.makefile check

stop-containers:
	make -f makefiles/db.makefile stop
	make -f makefiles/bind.makefile stop

start-api:
	make -f makefiles/api.makefile config
	make -f makefiles/api.makefile start
	sleep 2
	make -f makefiles/api.makefile check

stop-api:
	make -f makefiles/api.makefile stop

start: start-containers start-api

stop: stop-api stop-containers
