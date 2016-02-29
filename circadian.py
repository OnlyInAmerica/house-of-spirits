import time

from support.color import adjust_command_for_time
from support.hue import command_all_lights
from support.logger import get_logger
from support.time_utils import get_next_circadian_event, get_local_time

# Logging
logger = get_logger("circadian")


while 1:
        event, event_date = get_next_circadian_event()
        now = get_local_time()
        logger.info("Sleeping until " + event + " at " + event_date.strftime('%Y/%m/%d %I:%M:%S %p'))
        time.sleep((event_date - now).seconds)
        logger.info("Adjusting hue for " + event + " at " + get_local_time().strftime('%Y/%m/%d %I:%M:%S %p'))
        command = adjust_command_for_time({'transitiontime': 200})
        command_all_lights(command)
