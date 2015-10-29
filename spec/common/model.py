import json
import textwrap


class Model(object):

    @classmethod
    def from_json(cls, json_str):
        return cls.from_dict(json.loads(json_str))

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        model = cls()
        for key in data:
            val = data.get(key)
            if isinstance(val, dict):
                setattr(model, key, Model.from_dict(val))
            else:
                setattr(model, key, val)
        return model

    def to_dict(self):
        result = {}
        for key in self.__dict__:
            result[key] = getattr(self, key)
            if isinstance(result[key], Model):
                result[key] = result[key].to_dict()
        return result

    def __str__(self):
        return str(self.to_dict())


class Zone(object):

    def __init__(self, name, ttl=2400, serial=123456, records=[]):
        self.name = name
        self.ttl = ttl
        self.serial = serial
        self.records = set(records)
        assert self.name.endswith('.')

    def clone(self):
        return self.__class__(**self.__dict__)

    def zone_file_string(self):
        result = textwrap.dedent("""
        $ORIGIN {name}
        $TTL {ttl}

        {name} IN SOA ns1.{name} mail.{name} {serial} 100 101 102 103
        {name} IN NS ns1.{name}
        ns1.{name} IN A 127.0.0.1
        """).strip().format(**self.__dict__)

        for record in self.records:
            result += "\n{0}".format(record.zone_file_string())

        return result

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return "{0}{1}".format(self.__class__.__name__, str(self))


class Record(object):

    def __init__(self, name, type, data):
        self.name = name
        self.type = type.upper()
        self.data = data
        assert self.name.endswith('.')

    def clone(self):
        return self.__class__(**self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def zone_file_string(self):
        return "{name} IN {type} {data}".format(**self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return "{0}{1}".format(self.__class__.__name__, str(self))
