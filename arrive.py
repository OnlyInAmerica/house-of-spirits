import sys
import time

import settings
from support.hue import COMMAND_FULL_ON, COMMAND_OFF
from support.lock import is_locked, lock, unlock
from support.logger import get_logger

'''
Handle 'Arriving home' action.
Turn on stairwell for 30m, then turn off
'''

logger = get_logger("arrive")

ON_TIME_S = 60 * 20  # 30m

PROCESS_NAME = 'arrive'  # For use with lockfile to prevent multiple simultaneous operations


def perform_arrival():

    stairway = settings.ROOMS[4]

    stairway.update(COMMAND_FULL_ON)

    time.sleep(ON_TIME_S)

    stairway.update(COMMAND_OFF)


if __name__ == "__main__":
    # Invoke with `python arrive.py run` to run arrive program
    is_run_command = len(sys.argv) == 2 and sys.argv[1] == 'run'

    if is_run_command and not is_locked(PROCESS_NAME):
        lock(PROCESS_NAME)
        logger.info("Performing arrival")
        perform_arrival()
        unlock(PROCESS_NAME)
    elif is_locked():
        logger.info("Aborting run: lockfile exists")
