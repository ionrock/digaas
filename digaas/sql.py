import os

import aiomysql.sa
from sqlalchemy import Table, Column, Integer, MetaData, String

from digaas.config import cfg

metadata = MetaData()

_ENGINE = None
async def get_engine():
    global _ENGINE
    if not _ENGINE:
        print(cfg.CONF.sqlalchemy.engine)
        _ENGINE = await aiomysql.sa.create_engine(
            # cfg.CONF.sqlalchemy.engine,
            user='root',
            host='172.17.0.18',
            db='digaas',
            echo=True,
        )
    return _ENGINE

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

async def create_tables():
    engine = await get_engine()
    # tell sqlalchemy to create the tables
    metadata.create_all(engine)
create_tables()

