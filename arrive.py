import os
import time

import sys

import settings

from support.hue import COMMAND_FULL_ON, COMMAND_OFF
from support.logger import get_logger

'''
Handle 'Arriving home' action.
Turn on stairwell for 30m, then turn off
'''

logger = get_logger("arrive")

ON_TIME_S = 60 * 20  # 30m
LOCKFILE = 'arrive_lockfile'


def is_locked():
    try:
        lock_file = open(LOCKFILE, 'r')
        lock_file.close()
        return True

    except FileNotFoundError:
        return False


def lock():
    lock_file = open(LOCKFILE, 'w')
    lock_file.close()


def unlock():
    try:
        os.remove(LOCKFILE)
    except FileNotFoundError:
        pass


def perform_arrival():

    stairway = settings.ROOMS[4]

    stairway.update(COMMAND_FULL_ON)

    time.sleep(ON_TIME_S)

    stairway.update(COMMAND_OFF)


if __name__ == "__main__":
    # Invoke with `python arrive.py run` to run arrive program
    is_run_command = len(sys.argv) == 2 and sys.argv[1] == 'run'

    if is_run_command and not is_locked():
        lock()
        logger.info("Performing arrival")
        perform_arrival()
        unlock()
    elif is_locked():
        logger.info("Aborting run: lockfile exists")
