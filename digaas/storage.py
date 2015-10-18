from digaas.sql import get_engine
from sqlalchemy.sql import select

class Storage(object):

    @classmethod
    async def create(cls, obj):
        """Write the obj to the database. This sets obj.id and returns obj."""
        data = obj.to_dict()
        # ensure we get an auto-generated id on creates
        if 'id' in data:
            del data['id']
        query = obj.TABLE.insert().values(**data)
        result = (await get_engine()).execute(query)
        obj.id = result.inserted_primary_key[0]
        return obj

    @classmethod
    def update(cls, obj):
        pass

    @classmethod
    async def get(cls, id, obj_class):
        id = int(id)
        query = select([obj_class.TABLE]).where(obj_class.TABLE.c.id == id)
        result = await (await get_engine()).execute(query)
        if result.rowcount == 0:
            raise Exception("{0} with id={1} not found".format(
                            obj_class.__name__, id))
        row = result.fetchone()
        data = {k: v for k, v in zip(result.keys(), row)}
        return obj_class.from_dict(data)
