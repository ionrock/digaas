import logging

from digaas.sql import get_engine
from sqlalchemy.sql import select, update

LOG = logging.getLogger(__name__)

class Storage(object):

    @classmethod
    def _get_connection(cls):
        return get_engine().connect()

    @classmethod
    def create(cls, obj):
        """Write the obj to the database. This sets obj.id and returns obj."""
        data = obj.to_dict()
        # ensure we get an auto-generated id on creates
        data['id'] = 0

        query = obj.TABLE.insert().values(**data)

        conn = cls._get_connection()
        result = conn.execute(query)
        obj.id = result.inserted_primary_key[0]
        if obj.id <= 0:
            LOG.error("FAILED: object id is 0")
            LOG.error("  object: %s" % obj)
            LOG.error("  result.inserted_primary_key = %s" % result.inserted_primary_key)
            LOG.error(str(result.__dict__))
        result.close()
        conn.close()
        LOG.debug(str(obj))
        return obj

    @classmethod
    def update(cls, obj):
        data = obj.to_dict()
        if 'id' in data:
            del data['id']
        query = update(obj.TABLE) \
            .where(obj.TABLE.c.id == obj.id) \
            .values(**obj.to_dict())
        # TODO: success/failure detection
        conn = cls._get_connection()
        conn.execute(query)
        conn.close()

    @classmethod
    def get(cls, id, obj_class):
        id = int(id)
        query = select([obj_class.TABLE]).where(obj_class.TABLE.c.id == id)
        result = get_engine().execute(query)
        if result.rowcount == 0:
            raise Exception("{0} with id={1} not found".format(
                            obj_class.__name__, id))
        row = result.fetchone()
        data = {k: v for k, v in zip(result.keys(), row)}
        result.close()
        return obj_class.from_dict(data)


if __name__ == '__main__':
    from digaas.models import Observer
    observer = Observer(
        name='mrkrabs.com.',
        nameserver='127.0.0.1',
        start_time=11111111,
        interval=1,
        timeout=9,
        type='ZONE_CREATE',
        status='ACCEPTED',
    )

    # import ipdb; ipdb.set_trace()
    Storage.create(observer)


