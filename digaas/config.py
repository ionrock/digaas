import json
import os

class Config(object):

    _FILE = "/etc/digaas/digaas-config.json"
    _INSTANCE = None

    @classmethod
    def get(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls(cls._FILE)
        return cls._INSTANCE

    def __init__(self, filename):
        # don't use this directly. Use Config.get()
        data = self._load_config_file(filename)
        self.set_config_items(data)

    def set_config_items(self, data):
        self.redis_host = data.get('redis_host')
        self.redis_port = self.get_config_item_as_type(data, 'redis_port', int)
        self.redis_password = data.get('redis_password')
        self.graphite_host = data.get('graphite_host')
        self.graphite_port = self.get_config_item_as_type(data, 'graphite_port', int)
        self.dns_query_timeout = self.get_config_item_as_type(data, 'dns_query_timeout', float)

    def get_config_item_as_type(self, data, key, type=None):
        value = data.get(key)
        if value and type:
            try:
                return type(value)
            except ValueError as e:
                raise Exception(
                    'Failed to read config option %r as type %s (got value %s)'
                    % (key, type, value))
        return value

    def _load_config_file(self, filename):
        if not os.path.exists(filename):
            raise Exception("Failed to find config file: {0}".format(filename))
        try:
            return json.loads(open(filename, 'r').read())
        except Exception as e:
            raise Exception("Failed to load config file {0} -- {1}"
                            .format(filename, str(e)))

    def __str__(self):
        return str(self.__dict__)

CONFIG = Config.get()
