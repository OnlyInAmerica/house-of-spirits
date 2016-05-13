"""
This module manages getting and setting values stored in the system environment
"""
import os


def is_guest_mode() -> bool:
    return os.environ.get('guest_mode', 'false').lower() == 'true'


def set_guest_mode(enabled: bool):
    os.environ['guest_mode'] = 'true' if enabled else 'false'
