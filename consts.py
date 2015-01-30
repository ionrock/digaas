class Status:
    ACCEPTED       = "ACCEPTED"
    ERROR          = "ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    COMPLETED      = "COMPLETED"


class Condition:
    """These are used to determine when the poll request has succeeded"""
    SERIAL_NOT_LOWER = "serial_not_lower"
    ZONE_REMOVED     = "zone_removed"

    ALL = (SERIAL_NOT_LOWER, ZONE_REMOVED)
