import time

from phue import Light

from support.color import LIGHT_DAYTIME_XY, LIGHT_EVENING_XY
from support.hue import hue
from support.logger import get_logger
from support.time_utils import SUNRISE, SUNSET, get_next_circadian_event, get_local_time

# Logging
logger = get_logger("circadian")


def adjust_lights_for_event(circadian_event: str):
    for light in hue.get_light_objects(mode='id'):
        adjust_light_for_event(light, circadian_event)


def adjust_light_for_event(light: Light, circadian_event: str):
    if circadian_event is SUNRISE:
        hue.set_light(light, 'xy', LIGHT_DAYTIME_XY, transitiontime=200)
    elif circadian_event is SUNSET:
        hue.set_light(light, 'xy', LIGHT_EVENING_XY, transitiontime=200)
    else:
        logger.info("Unknown circadian event " + circadian_event)


while 1:
        event, event_date = get_next_circadian_event()
        now = get_local_time()
        logger.info("Sleeping until " + event + " at " + event_date.strftime('%Y/%m/%d %I:%M:%S %p'))
        time.sleep((event_date - now).seconds)
        logger.info("Adjusting hue for " + event + " at " + get_local_time().strftime('%Y/%m/%d %I:%M:%S %p'))
        adjust_lights_for_event(event)
