import time

import settings
from support.color import LIGHT_DAYTIME_XY, LIGHT_EVENING_XY
from support.logger import get_logger

# Logging
logger = get_logger("wakeup")

# Start at evening hue, min brightness. Fade to daytime hue, full brightness
# over 30m

bedroom = settings.ROOMS[3]

command = {'xy': LIGHT_EVENING_XY, 'bri': 1, 'on': True}

bedroom.update(command)
time.sleep(5)

command['bri'] = 254
command['xy'] = LIGHT_DAYTIME_XY
command['transitiontime'] = 10 * 60 * 30

bedroom.update(command)