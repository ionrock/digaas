import json


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
            setattr(model, key, data.get(key))
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
