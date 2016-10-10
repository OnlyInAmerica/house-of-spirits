import time

import settings
from support.color import LIGHT_DAYTIME_XY, LIGHT_EVENING_XY

# Start at evening hue, min brightness. Fade to daytime hue, full brightness
# over 30m
from support.logger import get_logger

logger = get_logger('wakeup')

living_room = settings.ROOMS[0]
hall = settings.ROOMS[1]
kitchen = settings.ROOMS[2]
bedroom = settings.ROOMS[3]

command = {'xy': LIGHT_EVENING_XY, 'bri': 1, 'on': True}

bedroom.update(command)
time.sleep(5)

command['bri'] = 254
command['xy'] = LIGHT_DAYTIME_XY
command['transitiontime'] = 10 * 60 * 30

bedroom.update(command)