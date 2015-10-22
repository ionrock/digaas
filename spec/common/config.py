import os
from oslo_config import cfg

cfg.CONF.register_group(cfg.OptGroup('digaas'))
cfg.CONF.register_group(cfg.OptGroup('bind'))
cfg.CONF.register_group(cfg.OptGroup('bind:docker'))

cfg.CONF.register_opts([
    cfg.StrOpt('endpoint'),
], group='digaas')

cfg.CONF.register_opts([
    cfg.StrOpt('host'),
    cfg.StrOpt('type', help="For now, 'docker' is the only value this can be"),
], group='bind')

cfg.CONF.register_opts([
    cfg.StrOpt('dir', help="Where zone files are stored in the container"),
    cfg.StrOpt('id', help="The container name or id"),
], group='bind:docker')


def _find_config_file(path='test.conf'):
    if not os.path.exists(path):
        raise Exception("Need config file '{0}' to run the tests".format(path))
    return path

cfg.CONF(args=[], default_config_files=[_find_config_file()])
