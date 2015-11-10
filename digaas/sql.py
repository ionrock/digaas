import sqlalchemy
from sqlalchemy import Table, Column, MetaData
from sqlalchemy import Integer, Float, String
from sqlalchemy.dialects.mysql import MEDIUMBLOB

from digaas.config import cfg

_ENGINE = None


# we want these logs to propagate up to the root logger, so they end up in the
# same log file as all other logs. We *don't* want these logs to print to
# stdout. What do we do?
#   1. if we remove all the handlers, it still prints to stdout
#   2. if we set `sql_logger.disabled = True`, it doesn't print anywhere
#   3. if we use a handler to output to the same log file, we get two copies of
#      the logs (one formatted and the other not)
#   4. if we set `sql_logger.propagate = False`, we lose our default formatting
# sql_logger = logging.getLogger('sqlalchemy.engine.base.Engine')
# sql_logger.handlers = [logging.FileHandler('/dev/null')]
# sql_logger.setLevel(logging.DEBUG)


def get_engine():
    global _ENGINE
    if not _ENGINE:
        _ENGINE = sqlalchemy.create_engine(
            cfg.CONF.sqlalchemy.engine,
            echo=False,
        )
    return _ENGINE

metadata = MetaData()
observers_table = Table(
    'observers', metadata,
    Column('id', Integer, nullable=False, primary_key=True,
           autoincrement=True),
    Column('name', String(512), nullable=False),
    Column('nameserver', String(512), nullable=False),
    Column('start_time', Integer, nullable=False),
    Column('duration', Float, nullable=True),
    Column('status', String(32), nullable=False),
    Column('interval', Integer, nullable=False),
    Column('timeout', Integer, nullable=False),
    Column('type', String(32), nullable=False),

    # used only when polling for an updated zone
    Column('serial', Integer, nullable=True),

    # used only when polling for specific record data
    Column('rdata', String(512), nullable=True),
    Column('rdatatype', String(16), nullable=True),
)

stats_table = Table(
    'stats', metadata,
    Column('id', Integer, nullable=False, primary_key=True,
           autoincrement=True),
    Column('start', Integer, nullable=False),
    Column('end', Integer, nullable=False),
    Column('status', String(32), nullable=False),
)

summary_table = Table(
    'summary', metadata,
    Column('id', Integer, nullable=False, primary_key=True,
           autoincrement=True),
    Column('stats_id', Integer, nullable=False),
    Column('view', String(48), nullable=False),
    Column('type', String(32), nullable=False),
    Column('average', Float, nullable=True),
    Column('median', Float, nullable=True),
    Column('min', Float, nullable=True),
    Column('max', Float, nullable=True),
    Column('per66', Float, nullable=True),
    Column('per75', Float, nullable=True),
    Column('per90', Float, nullable=True),
    Column('per95', Float, nullable=True),
    Column('per99', Float, nullable=True),
    Column('success_count', Integer, nullable=False),
    Column('error_count', Integer, nullable=False),
)

# this stores response times for every dns query performed.
# this should be append-only. no updates or deletes should occur to this table.
# note: use InnoDB which does row-level (rather than table-level) locking
dnsquery_table = Table(
    'dnsquery', metadata,
    Column('id', Integer, nullable=False, primary_key=True,
           autoincrement=True),
    Column('nameserver', String(32), nullable=False),
    Column('status', String(32), nullable=False),
    Column('timestamp', Integer, nullable=False),
    Column('duration', Float, nullable=False),
)

plots_table = Table(
    'plots', metadata,
    Column('id', Integer, nullable=False, primary_key=True,
           autoincrement=True),
    Column('stats_id', Integer, nullable=False),
    Column('type', String(32), nullable=False),
    Column('mimetype', String(255), nullable=False),
    Column('image', MEDIUMBLOB, nullable=False),
)

# tell sqlalchemy to create the tables
metadata.create_all(get_engine())
