
help:
	@echo "setup-dev - install a local development environment with redis and bind"

setup-dev: install-dev-depts configure-digaas restart-digaas check-digaas

install-dev-deps:
	apt-get install python-dev bind9 redis-server

configure-digaas:
	# write out digaas_config.py
	cp digaas/digaas_config.py.sample digaas/digaas_config.py
	sed -i -e "s/redis_host = None/redis_host = '127.0.0.1'/" digaas/digaas_config.py
	sed -i -e "s/redis_port = None/redis_port = 6379/" digaas/digaas_config.py

restart-digaas:
	python setup.py install
	service digaas-server stop
	sleep 2  # apparently service restart stops and starts too quickly
	service digaas-server restart

check-digaas:
	# grab the port
	$(eval DIGAAS_PORT := \
		$(shell . /etc/digaas/environment && echo $$DIGAAS_PORT))
	@echo "checking digaas is running on port $(DIGAAS_PORT)"
	curl localhost:$(DIGAAS_PORT)

