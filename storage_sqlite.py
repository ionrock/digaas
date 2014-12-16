import sqlite3

import model
import digaas_config as config

print "USING SQLITE STORAGE"

SQLITE_CLIENT = None
def get_sqlite_client():
    global SQLITE_CLIENT
    if SQLITE_CLIENT is None:
        SQLITE_CLIENT = sqlite3.connect(config.sqlite_db_file)
        SQLITE_CLIENT.execute("CREATE TABLE IF NOT EXISTS poll_requests("
            "id TEXT UNIQUE NOT NULL,"
            "zone_name TEXT NOT NULL,"
            "nameserver TEXT NOT NULL,"
            "serial INTEGER,"
            "start_time REAL NOT NULL,"
            "duration REAL,"
            "timeout INTEGER NOT NULL,"
            "frequency REAL NOT NULL,"
            "status TEXT NOT NULL,"
            "condition TEXT NOT NULL)")
    return SQLITE_CLIENT

# catch interrupts to commit and close connection gracefully
import signal
import sys
def handle_signal(signal, frame):
    print "closing sql connection"
    if SQLITE_CLIENT is not None:
        SQLITE_CLIENT.commit()
        SQLITE_CLIENT.close()
    sys.exit(0)
print "registering signal handler for sqlite cleanup"
signal.signal(signal.SIGINT, handle_signal)

def create_poll_request(poll_req):
    c = get_sqlite_client()
    c.execute("INSERT INTO poll_requests VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (poll_req.id,
              poll_req.zone_name,
              poll_req.nameserver,
              poll_req.serial,
              poll_req.start_time,
              poll_req.duration,
              poll_req.timeout,
              poll_req.frequency,
              poll_req.status,
              poll_req.condition))
    # committing on every create is slow. Ideally, we would commit less
    # frequently when load is high.
    c.commit()

def update_poll_request(poll_req):
    c = get_sqlite_client()
    c.execute("UPDATE poll_requests SET duration=?, status=? WHERE id=?",
              (poll_req.duration, poll_req.status, poll_req.id))
    c.commit()

def get_poll_request(id):
    c = get_sqlite_client()
    result = c.execute("SELECT * FROM poll_requests WHERE id=?", (id,))
    rows = result.fetchall()  # a list of tuples
    if rows:
        row = rows[0]
        return model.PollRequest(id         = row[0],
                                 zone_name  = row[1],
                                 nameserver = row[2],
                                 serial     = row[3],
                                 start_time = row[4],
                                 duration   = row[5],
                                 timeout    = row[6],
                                 frequency  = row[7],
                                 status     = row[8],
                                 condition  = row[9])
