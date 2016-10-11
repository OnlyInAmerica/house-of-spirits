"""
This module manages getting and setting inter-process state
"""

from datetime import datetime

import dateutil.parser
import os
import sqlite3

DB_FOLDER = './'
DB_FILENAME = 'state.db'
db = None

'''
    Weather
'''
KEY_CLOUD_COVER = 'cloud_cover'


def get_cloud_cover() -> float:
    coverage = _get_value(KEY_CLOUD_COVER)
    if not coverage:
        coverage = 0
    return coverage


def set_cloud_cover(coverage: float):
    _set_value(KEY_CLOUD_COVER, coverage)


'''
    Motion Sensing Mode
'''
KEY_MOTION_MODE = 'motion_mode'


def is_motion_enabled() -> bool:
    return _get_value(KEY_MOTION_MODE)


def set_motion_enabled(enabled: bool):
    _set_value(KEY_MOTION_MODE, enabled)


'''
    Guest Mode
'''
KEY_GUEST_MODE = 'guest_mode'


def is_guest_mode() -> bool:
    return _get_value(KEY_GUEST_MODE)


def set_guest_mode(enabled: bool):
    _set_value(KEY_GUEST_MODE, enabled)

'''
    Party Mode
'''
KEY_PARTY_MODE = 'party_mode'


def is_party_mode() -> bool:
    return _get_value(KEY_PARTY_MODE)


def set_party_mode(enabled: bool):
    _set_value(KEY_PARTY_MODE, enabled)


'''
    Last Room Motion
'''
KEY_PREFIX_LAST_ROOM_MOTION = 'motion_'


def set_room_last_motion_date(room_name: str, motion_date: datetime):
    _set_value(KEY_PREFIX_LAST_ROOM_MOTION + room_name.replace(' ', ''), motion_date.isoformat())


def get_room_last_motion_date(room_name: str) -> datetime:
    date_str = _get_value(KEY_PREFIX_LAST_ROOM_MOTION + room_name.replace(' ', ''))
    if date_str:
        try:
            return dateutil.parser.parse(date_str)
        except:
            return None

    return None

'''
    Room occupancy
'''
KEY_ROOM_OCCUPANCY = 'occupied_'


def set_room_occupied(room_name: str, enabled: bool):
    _set_value(KEY_ROOM_OCCUPANCY + room_name.replace(' ', ''), enabled)


def get_room_occupied(room_name: str) -> bool:
    return _get_value(KEY_ROOM_OCCUPANCY + room_name.replace(' ', ''))


def _get_value(key: str):
    """
    :return: a EID, Value pair, or False if no record found
    """
    db = _db_connect()

    value = db.execute("select value from key_value where key=?", (key,)).fetchone()

    if value is not None and value[0] is not None:
        print("Get %s . Results %s" % (key, value))
        return value[0]
    return False


def _set_value(key: str, value):
    print("Set %s -> %s" % (key, value))
    db = _db_connect()

    if _get_value(key):
        db.execute("update key_value set value=? where key=?", (value, key))
    else:
        db.execute("insert into key_value (key, value) values(?, ?)", (value, key))


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
