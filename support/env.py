"""
This module manages getting and setting inter-process state
"""
import json

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
    state = get_state()
    guest_mode = state.get('guest_mode', False)
    return guest_mode


def set_guest_mode(enabled: bool):
    state = get_state()
    state['guest_mode'] = enabled
    save_state(state)

