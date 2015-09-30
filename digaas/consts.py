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
