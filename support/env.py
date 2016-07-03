"""
This module manages getting and setting inter-process state
"""
import json
from datetime import datetime
import dateutil.parser

FILENAME = 'state'


def save_state(state: dict):
    state_file = open(FILENAME, 'w')
    state_file.write(json.dumps(state))
    state_file.close()


def get_state() -> dict:
    try:
        state_file = open(FILENAME, 'r')
        state = json.loads(state_file.read())
        state_file.close()
        return state
    except FileNotFoundError:
        return {}


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
    state = get_state()
    value = state.get(key, False)
    return value


def _set_value(key: str, value):
    state = get_state()
    state[key] = value
    save_state(state)
