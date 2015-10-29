SHELL := /bin/bash

GRAPHITE_TAG=digaas-graphite
GRAPHITE_CID=$(shell docker ps | grep $(GRAPHITE_TAG) | cut -f1 -d' ')
GRAPHITE_IP=$(shell docker inspect $(GRAPHITE_CID) | jq -r '.[0].NetworkSettings.IPAddress')

help:
	@echo "build        - build the docker graphite image"
	@echo "start 		- start the container running graphite"
	@echo "stop 		- kill and remove the container"
	@echo "check 		- check that graphite is running"
	@echo "clean        - delete the docker graphite image"
	@echo "               the host and container's rndc versions must match"
	@echo "ip           - print graphite's ip address to paste into configs"

build:
	cd dockerfiles && docker build -t $(GRAPHITE_TAG) -f ./Dockerfile.graphite .

start:
	docker run --name $(GRAPHITE_TAG) -d -t $(GRAPHITE_TAG)

stop:
	docker kill $(GRAPHITE_TAG) || true
	docker rm -f $(GRAPHITE_TAG) || true

clean:
	docker rmi -f $(GRAPHITE_TAG) || true

check:
	docker exec $(GRAPHITE_TAG) rndc status

ip:
	@echo $(GRAPHITE_IP)
