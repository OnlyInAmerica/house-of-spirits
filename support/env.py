"""
This module manages getting and setting inter-process state
"""

from datetime import datetime
from settings import ENV_DB_DIR
import dateutil.parser
import os
import sqlite3

DB_FOLDER = ENV_DB_DIR
DB_FILENAME = 'state.db'
db = None

'''
    Weather
'''
KEY_CLOUD_COVER = 'cloud_cover'


def get_cloud_cover() -> float:
    coverage = _get_value(KEY_CLOUD_COVER)
    if coverage is None:
        coverage = 0
    return float(coverage)


def set_cloud_cover(coverage: float):
    _set_value(KEY_CLOUD_COVER, coverage)


'''
    Motion Sensing Mode
'''
KEY_MOTION_MODE = 'motion_mode'


def is_motion_enabled() -> bool:
    return _get_bool_value(KEY_MOTION_MODE)


def set_motion_enabled(enabled: bool):
    _set_bool_value(KEY_MOTION_MODE, enabled)


'''
    Guest Mode
'''
KEY_GUEST_MODE = 'guest_mode'


def is_guest_mode() -> bool:
    return _get_bool_value(KEY_GUEST_MODE)


def set_guest_mode(enabled: bool):
    _set_bool_value(KEY_GUEST_MODE, enabled)

'''
    Party Mode
'''
KEY_PARTY_MODE = 'party_mode'


def is_party_mode() -> bool:
    return _get_bool_value(KEY_PARTY_MODE)


def set_party_mode(enabled: bool):
    _set_bool_value(KEY_PARTY_MODE, enabled)


'''
    Last Room Motion
'''


def set_room_last_motion_date(room_name: str, motion_date: datetime):

    last_motion_date_val = motion_date.isoformat()

    db = _db_connect()

    existing_room = db.execute("select id, last_motion_date from room_status where name=?", (room_name,)).fetchone()

    if existing_room is not None and existing_room[0] is not None:
        existing_id = existing_room[0]
        last_last_motion_date = existing_room[1]
        print("Update room '%s' id %d last motion from '%s' to '%s'" % (room_name, existing_id, last_last_motion_date, last_motion_date_val))
        db.execute("update room_status set last_motion_date=? where id=?", (last_motion_date_val, existing_id))
    else:
        print("Insert new room with last motion date %s" % last_motion_date_val)
        db.execute("insert into room_status (name, last_motion_date) values(?, ?)", (room_name, last_motion_date_val))
    db.commit()


def get_room_last_motion_date(room_name: str) -> datetime:

    db = _db_connect()

    print("Checking room '%s' last motion" % room_name)
    last_motion = db.execute("select last_motion_date from room_status where name=?", (room_name,)).fetchone()

    if last_motion is not None and last_motion[0] is not None:
        print("Room '%s' last motion '%s'" % (room_name, last_motion[0]))
        try:
            return dateutil.parser.parse(last_motion[0])
        except:
            pass

    return None

'''
    Room occupancy
'''


def set_room_occupied(room_name: str, occupied: bool):

    occupied_val = 1 if occupied else 0

    db = _db_connect()

    existing_room = db.execute("select id, occupied from room_status where name=?", (room_name,)).fetchone()

    if existing_room is not None and existing_room[0] is not None:
        existing_id = existing_room[0]
        was_occupied = existing_room[1]
        print("Update room '%s' occupied from '%s' to '%s'" % (room_name, was_occupied, occupied_val))
        db.execute("update room_status set occupied=? where id=?", (occupied_val, existing_id))
    else:
        print("Insert new room with occupied %s" % occupied_val)
        db.execute("insert into room_status (name, occupied) values(?, ?)", (room_name, occupied_val))
    db.commit()


def get_room_occupied(room_name: str) -> bool:
    db = _db_connect()

    print("Checking room '%s' occupied" % room_name)
    occupied = db.execute("select occupied from room_status where name=?", (room_name,)).fetchone()

    if occupied is not None and occupied[0] is not None:
        print("Room '%s' occupied '%s'" % (room_name, occupied[0]))
        return True if occupied[0] == 1 else False
    return False


'''
    Private API
'''


def _get_bool_value(key: str) -> bool:
    value = _get_value(key)
    print("Bool key '%s' has value '%s'" % (key, not (value is None or value == '0')))
    if value is None or value == '0':
        return False
    return True


def _get_value(key: str):
    db = _db_connect()

    value = db.execute("select value from key_value where key=?", (key,)).fetchone()

    if value is not None and value[0] is not None:
        print("Get %s . Result '%s'" % (key, value[0]))
        return value[0]
    return None


def _set_bool_value(key: str, value: bool):
    _set_value(key, '1' if value else '0')


def _set_value(key: str, value):
    db = _db_connect()

    existing_value = _get_value(key)
    if existing_value is not None:
        print("Update key '%s' value from '%s' to '%s'" % (key, existing_value, value))
        db.execute("update key_value set value=? where key=?", (value, key))
    else:
        print("Insert %s -> %s" % (key, value))
        db.execute("insert into key_value (key, value) values(?, ?)", (key, value))
    db.commit()


def _get_schema_version(db):
    # user_version is per database value, its used here
    # to store the version of the schema
    return db.execute(r"PRAGMA user_version").fetchone()[0]


def _create_schema(start_fresh=False):
    try:
        if start_fresh:
            db_path = os.path.join(DB_FOLDER, DB_FILENAME)
            if os.path.exists(db_path):
                # Preserve one backup, for evidence!
                os.rename(db_path, db_path + ".old")

        with _db_connect() as db:
            # fall through each block updating the user_version each time
            # so that schema changes can be correctly applied
            version = _get_schema_version(db)
            if version == 0:
                db.execute(r"create table room_status ("
                           r"id integer primary key AUTOINCREMENT,"
                           r"name text NOT NULL,"
                           r"occupied int DEFAULT 0,"
                           r"last_motion_date text"
                           r")")
                db.execute(r"create table key_value ("
                           r"id integer primary key AUTOINCREMENT,"
                           r"key text NOT NULL,"
                           r"value text"
                           r")")
                db.execute(r"PRAGMA user_version=1")
    except:
        #logger.exception("Failed in creating database schema while {}starting fresh".format("" if start_fresh else "not "))
        if not start_fresh:
            return _create_schema(start_fresh=True)
        return False
    return True


def _db_connect():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    db_path = os.path.join(DB_FOLDER, DB_FILENAME)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

# Create the database on startup
_create_schema()
print("Create schema!")
