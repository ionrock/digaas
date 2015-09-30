import os

import sqlalchemy
from sqlalchemy import Table, Column, Integer, MetaData, String

from digaas.config import cfg

_ENGINE = None
def get_engine():
    global _ENGINE
    if not _ENGINE:
        _ENGINE = sqlalchemy.create_engine(
            cfg.CONF.sqlalchemy.engine,
            echo=True,
        )
    return _ENGINE

metadata = MetaData()
observers_table = Table('observers', metadata,
    Column('id', Integer, nullable=False, primary_key=True),
    Column('name', String(512), nullable=False),
    Column('nameserver', String(512), nullable=False),
    Column('start_time', Integer, nullable=False),
    Column('duration', Integer, nullable=True),
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

# tell sqlalchemy to create the tables
metadata.create_all(get_engine())
