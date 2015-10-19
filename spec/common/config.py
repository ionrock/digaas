import os
from oslo_config import cfg

cfg.CONF.register_group(cfg.OptGroup('digaas'))
cfg.CONF.register_group(cfg.OptGroup('bind'))

cfg.CONF.register_opts([
    cfg.StrOpt('endpoint'),
], group='digaas')

cfg.CONF.register_opts([
    cfg.StrOpt('host'),
], group='bind')

def _find_config_file(path='test.conf'):
    if not os.path.exists(path):
        raise Exception("Need config file '{0}' to run the tests".format(path))
    return path

cfg.CONF(args=[], default_config_files=[_find_config_file()])
