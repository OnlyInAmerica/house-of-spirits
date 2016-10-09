"""
This module manages getting and setting inter-process state
"""
from tinydb import TinyDB, Query
from datetime import datetime

import dateutil.parser

DB_FILENAME = 'state.db'
db = None

def is_guest_mode() -> bool:
    return _get_value('guest_mode')


def set_guest_mode(enabled: bool):
    _set_value('guest_mode', enabled)


def is_party_mode() -> bool:
    return _get_value('party_mode')


def set_party_mode(enabled: bool):
    _set_value('party_mode', enabled)


def set_room_last_motion_date(room_name: str, motion_date: datetime):
    _set_value('motion_' + room_name.replace(' ', ''), motion_date.isoformat())


def get_room_last_motion_date(room_name: str) -> datetime:
    date_str = _get_value('motion_' + room_name.replace(' ', ''))
    if date_str:
        try:
            return dateutil.parser.parse(date_str)
        except:
            return None

    return None


def _get_value(key: str):
    db = _connect_db()
    KeyValue = Query()
    result = db.get(KeyValue.key == key)
    print("Get %s . Results %s" % (key, result))

    if result is not None:
        return result['value']
    return False


def _set_value(key: str, value):
    print("Set %s -> %s" % (key, value))
    db = _connect_db()
    KeyValue = Query()
    result = db.get(KeyValue.key == key)
    if result:
        db.update({'value': value}, KeyValue.key == key)
    else:
        db.insert({'key': key, 'value': value})


def _connect_db():
    global db
    if db is None:
        db = TinyDB(DB_FILENAME)
    return db
