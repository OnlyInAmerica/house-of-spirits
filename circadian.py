import time

import copy

from support.color import get_next_circadian_color
from support.env import get_room_occupied
from support.hue import command_all_lights, hue
from support.logger import get_logger
from support.room import LightsOnDuringDayRoom
from support.time_utils import get_local_time
from settings import ROOMS

# Logging
logger = get_logger("circadian")

while 1:
    now = get_local_time()
    next_color_date, next_color = get_next_circadian_color(date=now)

    sleep_time_s = (next_color_date - now).seconds
    logger.info("Sleeping until %s at %s", next_color.name, next_color_date.strftime('%Y/%m/%d %I:%M:%S %p'))
    time.sleep(sleep_time_s + 30)  # Add padding to compensate for sleep inaccuracy
    logger.info("Adjusting hue for %s", next_color.name)
    command = next_color.apply_to_command({'transitiontime': 60 * 10})  # 60 s transition

    if next_color.name == 'Day':
        lights = []
        for room in ROOMS:
            if not isinstance(room, LightsOnDuringDayRoom):
                lights += room.lights
        hue.set_light(lights, command)
    elif next_color.name == 'Late Afternoon':
        # This transitions the lights from off to on, so we should turn on rooms
        # that are occupied (in addition to applying the circadian hue)
        on_plus_command = copy.deepcopy(command)
        on_plus_command['on'] = True

        for room in ROOMS:
            if get_room_occupied(room.name):
                logger.info("Turning on occupied room %s for Late Afternoon transition" % room.name)
                room.update(on_plus_command)
            else:
                room.update(command)
    else:
        command_all_lights(command)
