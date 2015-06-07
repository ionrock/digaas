BIND_CONF = 'scripts/named.conf.options'
ZONE_FILE_DIR = $(shell cat $(BIND_CONF) | grep directory | sed 's/.*directory "\([^"]*\)".*/\1/')
BIND_LOG_DIR = $(shell cat $(BIND_CONF) | grep log | grep file | sed 's/.*file "\([^"]*\)\/bind[.]log".*/\1/')

help:
	@echo "setup-dev - install a local development environment with redis and bind"
	@echo "restart-digaas - restart the digaas server"

setup-dev: _install-dev-deps _configure-bind _configure-digaas restart-digaas check-digaas

_install-dev-deps:
	apt-get install python-pip python-dev bind9 redis-server

_configure-digaas:
	# write out digaas_config.py
	cp digaas/digaas_config.py.sample digaas/digaas_config.py
	sed -i -e "s/redis_host = None/redis_host = '127.0.0.1'/" digaas/digaas_config.py
	sed -i -e "s/redis_port = None/redis_port = 6379/" digaas/digaas_config.py
	python setup.py install

_configure-bind:
	# disable bind apparmor restrictions
	mkdir -p /etc/apparmor.d/disable
	touch /etc/apparmor.d/disable/usr.sbin.named
	service apparmor restart

	mkdir -p $(ZONE_FILE_DIR)
	mkdir -p $(BIND_LOG_DIR)
	cp $(BIND_CONF) /etc/bind/named.conf.options
	chown -R bind:bind $(ZONE_FILE_DIR)
	chown -R bind:bind $(BIND_LOG_DIR)
	service bind9 restart

restart-digaas:
	service digaas-server stop
	sleep 2  # apparently service restart stops and starts too quickly
	service digaas-server restart

check-digaas:
	# grab the port
	$(eval DIGAAS_PORT := \
		$(shell . /etc/digaas/environment && echo $$DIGAAS_PORT))
	@echo "checking digaas is running on port $(DIGAAS_PORT)"
	curl localhost:$(DIGAAS_PORT) ; echo

cleanout-zones:
	./scripts/cleanout_zones.sh $(ZONE_FILE_DIR)
