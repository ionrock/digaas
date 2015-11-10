class ObserverStatuses(object):
    def __init__(self):
        self.ACCEPTED = 'ACCEPTED'
        self.COMPLETE = 'COMPLETE'
        self.ERROR = 'ERROR'
        self.INTERNAL_ERROR = 'INTERNAL_ERROR'


class ObserverTypes(object):
    def __init__(self):
        self.ZONE_CREATE = 'ZONE_CREATE'
        self.ZONE_UPDATE = 'ZONE_UPDATE'
        self.ZONE_DELETE = 'ZONE_DELETE'
        self.RECORD_CREATE = 'RECORD_CREATE'
        self.RECORD_UPDATE = 'RECORD_UPDATE'
        self.RECORD_DELETE = 'RECORD_DELETE'


class ObserverStatsStatuses(ObserverStatuses):
    pass


class DnsQueryStatuses(object):
    def __init__(self):
        self.SUCCESS = 'SUCCESS'
        self.TIMEOUT = 'TIMEOUT'


class PlotTypes(object):
    def __init__(self):
        self.PROPAGATION_BY_TYPE = 'PROPAGATION_BY_TYPE'
        self.PROPAGATION_BY_NAMESERVER = 'PROPAGATION_BY_NAMESERVER'
        self.QUERY = 'QUERY'


class SummaryViews(object):
    def __init__(self):
        self.QUERIES = 'QUERIES'
        self.QUERIES_OVER_THRESHOLD = 'QUERIES_OVER_THRESHOLD'
        self.OBSERVERS_BY_TYPE = 'OBSERVERS_BY_TYPE'
        self.OBSERVERS_BY_NAMESERVER = 'OBSERVERS_BY_NAMESERVER'
