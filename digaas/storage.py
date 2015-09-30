from digaas.sql import get_engine, observers_table
from sqlalchemy.sql import select

class ObjectStorage(object):

    def create(self, obj):
        """Write the obj to the database. This sets obj.id and returns obj."""
        data = obj.to_dict()
        # ensure we get an auto-generated id on creates
        if 'id' in data:
            del data['id']
        query = observers_table.insert().values(**data)
        result = get_engine().execute(query)
        obj.id = result.inserted_primary_key
        return obj

    def update(self, obj):
        pass

    def get(self, id, obj_class):
        query = select([observers_table]).where(obj_class.TABLE.c.id == id)
        result = get_engine().execute(query)
        if result.rowcount == 0:
            raise Exception("{0} with id={1} not found".format(
                            obj_class.__name__, id))
        row = result.fetchone()
        data = {k: v for k, v in zip(result.keys(), row)}
        return obj_class.from_dict(data)

if __name__ == '__main__':
    from digaas.models import Observer

#    obs = Observer(
#        name='poo.com.',
#        nameserver='ns.poo.com.',
#        start_time=1234567890,
#        interval=1,
#        timeout=300,
#        status=Observer.Status.ACCEPTED,
#        type=Observer.Type.ZONE_CREATE,
#    )
#    ObjectStorage().create(obs)

    obj = ObjectStorage().get(1, Observer)
    print(obj.to_dict())
