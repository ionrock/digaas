SHELL := /bin/bash

MYSQL_TAG=digaas-mysql
MYSQL_CID=$(shell docker ps | grep $(MYSQL_TAG) | cut -f1 -d' ')
MYSQL_IP=$(shell docker inspect $(MYSQL_CID) | jq -r '.[0].NetworkSettings.IPAddress')

help:
	@echo "build        - build the docker mysql image"
	@echo "start        - start the container running mysql"
	@echo "stop         - kill and remove the container"
	@echo "check        - check that mysql is running"
	@echo "clean        - delete the docker mysql image"
	@echo "               the host and container's mysql client verions must match"
	@echo "ip           - print the mysql's ip address to paste into configs"
	@echo "sqlengine    - print the sqlalchemy engine to paste into configs"
	@echo "shell        - start the mysql shell"

build:
	cd dockerfiles && docker build -t $(MYSQL_TAG) -f ./Dockerfile.mysql .

start:
	@docker run --name $(MYSQL_TAG) -d -t $(MYSQL_TAG)

stop:
	docker kill $(MYSQL_TAG) || true
	docker rm -f $(MYSQL_TAG) || true

clean:
	docker rmi -f $(MYSQL_TAG) || true

check:
	mysql -h $(MYSQL_IP) -u root -e status

ip:
	@echo $(MYSQL_IP)

sqlengine:
	@echo "mysql://root@$(MYSQL_IP)/digaas"

shell:
	mysql -h $(MYSQL_IP) -u root
