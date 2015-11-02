import os
from oslo_config import cfg

# look for the file in these locations, in order. use the first file found.
_LOCATIONS = (
    os.path.realpath('digaas.conf'),
    os.path.realpath('etc/digaas.conf'),
    '/etc/digaas/digaas.conf',
)

cfg.CONF.register_group(cfg.OptGroup('sqlalchemy'))
cfg.CONF.register_group(cfg.OptGroup('graphite'))
cfg.CONF.register_group(cfg.OptGroup('digaas'))

cfg.CONF.register_opts([
    cfg.StrOpt('engine'),
], group='sqlalchemy')

cfg.CONF.register_opts([
    cfg.StrOpt('host'),
    cfg.IntOpt('port'),
], group='graphite')

cfg.CONF.register_opts([
    cfg.FloatOpt('dns_query_timeout', default=2.0,
                 help="the timeout on low-level dns queries"),
    cfg.StrOpt('tmp_dir', default='/tmp/digaas',
               help="a place to put temporary files (like gnuplot files)"),
], group='digaas')


def _find_config_file():
    for location in _LOCATIONS:
        if os.path.exists(location):
            print('Using config file %s' % location)
            return location
    raise Exception("Failed to find digaas.conf at any of these paths: {0}"
                    .format(_LOCATIONS))

cfg.CONF(args=[], default_config_files=[_find_config_file()])
