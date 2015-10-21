from digaas.sql import observers_table
from digaas.consts import ObserverStatuses, ObserverTypes


class Observer(object):
    TABLE = observers_table
    TYPES = ObserverTypes()
    STATUSES = ObserverStatuses()

    def __init__(self, name, nameserver, start_time, interval, timeout,
                 type, status=None, id=None, duration=None, serial=None,
                 rdata=None, rdatatype=None):
        """
        :param name: the dns name to query for
        :param nameserver: the nameserver to query
        :param start_time: the start_time used to compute the duration
        :param interval: determines how frequently to poll the nameserver
        :param timeout: how long to poll the nameserver before timing out
        :param status: the status of the request. See ObserverStatuses.
        :param type: the type of change being observed. See ObserverTypes.
        :param id: the primary key from the database
        :param duration: how long after start_time the change was observed
        :param serial: only for ZONE_UPDATE type; a zone is considered updated
            when its serial is greater than or equal to this
        :param rdata: only for RECORD_* type; the record data to look for
        :param rdatatype: only for RECORD_* type; the record type to check
        """
        self.id = id
        self.name = name
        self.nameserver = nameserver
        self.start_time = start_time
        self.interval = interval
        self.timeout = timeout
        self.status = status
        self.duration = duration
        self.serial = serial
        self.rdata = rdata
        self.rdatatype = rdatatype
        self.type = type

    def validate(self):
        if self.type not in self.TYPES.__dict__:
            raise ValueError("Type {0} not in {1}".format(
                self.type, tuple(self.TYPES.__dict__.keys())))

        if self.type == self.TYPES.ZONE_UPDATE and self.serial is not None:
            raise ValueError("Serial must not be null for type {0}"
                             .format(self.type))

        record_types = (self.TYPES.RECORD_CREATE, self.TYPES.RECORD_UPDATE,
                        self.TYPES.RECORD_DELETE)
        if self.type in record_types \
                and self.rdata is not None \
                and self.rdatatype is not None:
            raise ValueError("rdata and rdatatype must both not be null for "
                             "RECORD_* types")

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return dict(self.__dict__)

    def __str__(self):
        return "{0}{1}".format(self.__class__.__name__, str(self.to_dict()))
