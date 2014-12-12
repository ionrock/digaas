import uuid

def check_has_keys(data, *args):
    for key in args:
        if key not in data:
            raise ValueError("Missing '{0}' from {1}. Expecting keys {2}"
                             .format(key, data, args))


class PollRequest(object):

    def __init__(self, zone_name, nameserver, serial, time, id=None,
                 status=None):
        """
        :param id: if None, generate a uuid.
        """
        self.zone_name = zone_name
        self.nameserver = nameserver
        self.serial = int(serial)
        self.time = float(time) if time is not None else None
        self.id = str(uuid.uuid4())
        self.status = status

    @classmethod
    def from_dict(cls, data):
        """Create a PollRequest from a dictionary.

        :param data: A dictionary, which is validated
        :raises ValueError: On failed validation.
        """
        check_has_keys(data, 'zone_name', 'nameserver', 'time', 'serial')
        zone_name = data.get('zone_name')
        nameserver = data.get('nameserver')
        time = float(data.get('time'))  # TODO: to timestamp?
        serial = int(data.get('serial'))
        id = data.get('id')
        status = data.get('status')
        return PollRequest(zone_name=zone_name,
                           nameserver=nameserver,
                           time=time,
                           serial=serial,
                           id=id,
                           status=status)

    def to_dict(self):
        return dict(zone_name=self.zone_name,
                    nameserver=self.nameserver,
                    time=self.time,
                    serial=self.serial,
                    id=self.id,
                    status=self.status)
