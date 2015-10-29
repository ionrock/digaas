from digaas import consts
from digaas.sql import observers_table
from digaas.sql import stats_table
from digaas.sql import summary_table


class BaseModel(object):

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return dict(self.__dict__)

    def __str__(self):
        return "{0}{1}".format(self.__class__.__name__, str(self.to_dict()))


class Observer(BaseModel):
    TABLE = observers_table
    TYPES = consts.ObserverTypes()
    STATUSES = consts.ObserverStatuses()

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

        if self.type == self.TYPES.ZONE_UPDATE and self.serial is None:
            raise ValueError("Serial must not be null for type {0}"
                             .format(self.type))

        record_types = (self.TYPES.RECORD_CREATE, self.TYPES.RECORD_UPDATE,
                        self.TYPES.RECORD_DELETE)
        if self.type in record_types \
                and (self.rdata is None or self.rdatatype is None):
            raise ValueError("rdata and rdatatype must both not be null for "
                             "RECORD_* types")


class ObserverStats(BaseModel):
    TABLE = stats_table
    STATUSES = consts.ObserverStatsStatuses()

    def __init__(self, start, end, id=None, status=None):
        """
        :param start: the lower bound of the range of observers to select
        :param end: the upper bound of the range of observers to select
        :param id: the primary key from the database
        :param status: the status of the asynchronous request
        """
        self.start = start
        self.end = end
        self.id = id
        self.status = status

    def validate(self):
        if self.start is None or self.end is None:
            raise ValueError("start and end must both not be null")
        if self.start > self.end:
            raise ValueError("start must be before end")


class Summary(BaseModel):
    TABLE = summary_table
    TYPES = consts.SummaryTypes()

    def __init__(self, stats_id, type, average, median, min, max, per66,
                 per75, per90, per95, per99, success_count, error_count,
                 id=None):
        """The average/median/min/max are for the data in the range of time
        select by the associated ObserverStats request. The perNN fields are
        percentiles. We store the 66, 75, 90, 95, and 99 percentiles. The
        median is the 50th percentile and the max is the 100th percentile.

        :param id: the primary key from the database
        :param stats_id: the id of the associated ObserverStats
        :param type: the type of summary statistics
        """
        self.id = id
        self.stats_id = stats_id
        self.type = type
        self.average = average
        self.median = median
        self.min = min
        self.max = max
        self.per66 = per66
        self.per75 = per75
        self.per90 = per90
        self.per95 = per95
        self.per99 = per99
        self.success_count = success_count
        self.error_count = error_count
