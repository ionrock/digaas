SHELL := /bin/bash

BIND_TAG=digaas-bind
BIND_CID=$(shell docker ps | grep $(BIND_TAG) | cut -f1 -d' ')
BIND_IP=$(shell docker inspect $(BIND_CID) | jq -r '.[0].NetworkSettings.IPAddress')

RNDC_KEY=$(shell find . -name "rndc.key")

help:
	@echo "build        - build the docker bind image"
	@echo "start 		- start the container running bind"
	@echo "stop 		- kill and remove the container"
	@echo "check 		- check that bind is running"
	@echo "clean        - delete the docker bind image"
	@echo "               the host and container's rndc versions must match"
	@echo "ip           - print bind's ip address to paste into configs"

build:
	cd dockerfiles && docker build -t $(BIND_TAG) -f ./Dockerfile.bind .

start:
	docker run --name $(BIND_TAG) -d -t $(BIND_TAG)

stop:
	docker kill $(BIND_TAG) || true
	docker rm -f $(BIND_TAG) || true

clean:
	docker rmi -f $(BIND_TAG) || true

check:
	docker exec $(BIND_TAG) rndc status

ip:
	@echo $(BIND_IP)
