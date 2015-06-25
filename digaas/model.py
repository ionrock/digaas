import uuid

from digaas import consts

class PollRequest(object):

    def __init__(self, query_name, nameserver, serial, start_time, condition,
                 timeout, frequency, rdatatype=None, duration=None, id=None, status=None):
        """
        :param id: if None, generate a uuid.
        """
        self.query_name = query_name
        self.nameserver = nameserver
        self.rdatatype = rdatatype
        self.serial = int(serial)
        self.start_time = float(start_time) if start_time is not None else None
        self.duration = float(duration) if duration is not None else None
        self.id = id if id is not None else str(uuid.uuid4())
        self.status = status
        self.condition = condition
        self.timeout = int(timeout)
        self.frequency = float(frequency)

    @classmethod
    def validate(cls, data):
        keys = ('query_name', 'nameserver', 'start_time', 'serial', 'condition',
                'timeout', 'frequency')
        for key in keys:
            if key not in data:
                raise ValueError("Missing '{0}' from {1}. Expecting keys {2}"
                                 .format(key, data, keys))

        condition = data['condition']
        if not consts.Condition.validate_condition(condition):
            raise ValueError("Invalid condition '{0}'. Valid conditions: {1}"
                             .format(condition, consts.Condition.ALL))

        if condition.startswith(consts.Condition.DATA_EQUALS):
            rdatatype = data.get('rdatatype')
            if not rdatatype:
                raise ValueError("Must provide 'rdatatype' field with '{0}' condition"
                                 .format(condition))
            valid_record_types = ('NS', 'A', 'AAAA')
            if not rdatatype.upper() in valid_record_types:
                raise ValueError("rdatatype {0} is not supported. Valid record types: {1}"
                                 .format(rdatatype, valid_record_types))

    @classmethod
    def from_dict(cls, data):
        return PollRequest(query_name=data.get('query_name'),
                           nameserver=data.get('nameserver'),
                           rdatatype=data.get('rdatatype'),
                           start_time=data.get('start_time'),
                           duration=data.get('duration'),
                           serial=data.get('serial'),
                           id=data.get('id'),
                           status=data.get('status'),
                           condition=data.get('condition'),
                           timeout=data.get('timeout'),
                           frequency=data.get('frequency'))

    def to_dict(self):
        return dict(query_name=self.query_name,
                    nameserver=self.nameserver,
                    rdatatype=self.rdatatype,
                    start_time=self.start_time,
                    duration=self.duration,
                    serial=self.serial,
                    id=self.id,
                    status=self.status,
                    condition=self.condition,
                    timeout=self.timeout,
                    frequency=self.frequency)


class StatsRequest(object):

    def __init__(self, start_time, end_time, status=None, id=None, image_id=None):
        self.id = id if id is not None else str(uuid.uuid4())
        self.start_time = float(start_time) if start_time is not None else None
        self.end_time = float(end_time)
        self.image_id = image_id
        self.status = status

    @classmethod
    def validate(cls, data):
        keys = ('start_time', 'end_time')
        for key in keys:
            if key not in data:
                raise ValueError("Missing '{0}' from {1}. Expecting keys {2}"
                                 .format(key, data, keys))

        start_time = int(data['start_time'])
        end_time = int(data['end_time'])
        if end_time <= start_time:
            raise ValueError("End time {0} must come after the start time {1}"
                             .format(end_time, start_time))


    @classmethod
    def from_dict(cls, data):
        return StatsRequest(
            status=data.get('status'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            id=data.get('id'),
            image_id=data.get('image_id'),
        )

    def to_dict(self):
        return dict(
            status=self.status,
            start_time=self.start_time,
            end_time=self.end_time,
            id=self.id,
            image_id=self.image_id,
        )
