import uuid

import poll

class PollRequest(object):

    def __init__(self, zone_name, nameserver, serial, start_time, condition,
                 timeout, frequency, duration=None, id=None, status=None):
        """
        :param id: if None, generate a uuid.
        """
        self.zone_name = zone_name
        self.nameserver = nameserver
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
        keys = ('zone_name', 'nameserver', 'start_time', 'serial', 'condition',
                'timeout', 'frequency')
        for key in keys:
            if key not in data:
                raise ValueError("Missing '{0}' from {1}. Expecting keys {2}"
                                 .format(key, data, keys))

        condition = data['condition']
        if condition not in poll.Conditions.ALL:
            raise ValueError("Invalid condition '{0}'. Must be one of {1}"
                             .format(condition, poll.Conditions.ALL))


    @classmethod
    def from_dict(cls, data):
        return PollRequest(zone_name=data.get('zone_name'),
                           nameserver=data.get('nameserver'),
                           start_time=data.get('start_time'),
                           duration=data.get('duration'),
                           serial=data.get('serial'),
                           id=data.get('id'),
                           status=data.get('status'),
                           condition=data.get('condition'),
                           timeout=data.get('timeout'),
                           frequency=data.get('frequency'))

    def to_dict(self):
        return dict(zone_name=self.zone_name,
                    nameserver=self.nameserver,
                    start_time=self.start_time,
                    duration=self.duration,
                    serial=self.serial,
                    id=self.id,
                    status=self.status,
                    condition=self.condition,
                    timeout=self.status,
                    frequency=self.frequency)
