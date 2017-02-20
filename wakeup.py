import time

import sys

import settings
from support.color import LIGHT_DAYTIME_XY, LIGHT_EVENING_XY

# Start at evening hue, min brightness. Fade to daytime hue, full brightness
# over 30m
from support.logger import get_logger
from support.env import is_vacation_mode

logger = get_logger('wakeup')

if is_vacation_mode():
    logger.info("Aborting wakeup: Vacation mode is enabled")
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