import datetime
import time

import sys

import settings
from support.color import LIGHT_DAYTIME_XY, LIGHT_EVENING_XY

# Start at evening hue, min brightness. Fade to daytime hue, full brightness
# over 30m
from support.logger import get_logger
from support.env import is_vacation_mode, set_vacation_mode
from support.time_utils import get_local_time

VACATION_MODE_MOTION_TIMEOUT = datetime.timedelta(hours=12)


def on_vacation() -> bool:

    now = get_local_time()

    # Use Hall as the motion trigger for vacation mode since
    # it gates the bedroom
    hall = settings.ROOMS[1]
    last_motion = hall.get_last_motion()

    since_motion = now - last_motion
    timed_out = since_motion > VACATION_MODE_MOTION_TIMEOUT

    logger.info("Setting Vacation mode to %r based on last hallway motion %s" % (timed_out, last_motion))

    set_vacation_mode(timed_out)
    return timed_out

logger = get_logger('wakeup')

if on_vacation():
    logger.info("Aborting wakeup: On Vacation")
    sys.exit(0)

bedroom = settings.ROOMS[3]

if bedroom.is_lit():
    logger.info("Aborting wakeup: Bedroom is already lit")
    sys.exit(0)

command = {'xy': LIGHT_EVENING_XY, 'bri': 1, 'on': True}

bedroom.update(command)
time.sleep(5)

command['bri'] = 254
command['xy'] = LIGHT_DAYTIME_XY
command['transitiontime'] = 10 * 60 * 30

bedroom.update(command)
logger.info("Performed wakeup")