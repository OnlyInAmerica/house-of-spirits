"""
This module manages getting and setting inter-process state
"""
from typing import Any

from tinydb import TinyDB, Query
from datetime import datetime

import dateutil.parser

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


KEY_TO_EID_MAP = {}


def _get_value(key: str) -> Any:
    """
    :return: a EID, Value pair, or False if no record found
    """
    db = _connect_db()

    if key in KEY_TO_EID_MAP:
        return _get_value_by_eid(KEY_TO_EID_MAP[key])

    KeyValue = Query()
    result = db.get(KeyValue.key == key)
    print("Get %s . Results %s" % (key, result))

    if result is not None:
        KEY_TO_EID_MAP[key] = result.eid
        return result['value']
    return False


def _get_value_by_eid(eid: int) -> Any:
    db = _connect_db()
    return db.get(eid=eid)


def _set_value(key: str, value):
    print("Set %s -> %s" % (key, value))
    db = _connect_db()

    if key in KEY_TO_EID_MAP:
        _set_value_by_eid(KEY_TO_EID_MAP[key], value)
        return

    KeyValue = Query()
    result = db.get(KeyValue.key == key)
    if result:
        db.update({'value': value}, KeyValue.key == key)
    else:
        db.insert({'key': key, 'value': value})


def _set_value_by_eid(eid: int, value):
    db.update({'value': value}, eids=[eid])


def _connect_db():
    global db
    if db is None:
        db = TinyDB(DB_FILENAME)
    return db
