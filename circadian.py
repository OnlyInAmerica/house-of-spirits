import time

from support.color import get_next_circadian_color
from support.hue import command_all_lights
from support.logger import get_logger
from support.time_utils import get_local_time

# Logging
logger = get_logger("circadian")


while 1:
        next_color = get_next_circadian_color()
        next_color_date = next_color.trigger_date_function()

        now = get_local_time()
        logger.info("Sleeping until " + next_color.name + " at " + next_color_date.strftime('%Y/%m/%d %I:%M:%S %p'))
        time.sleep((next_color_date - now).seconds + 30)  # Add a buffer to compensate for sleep inaccuracy
        logger.info("Adjusting hue for " + next_color_date + " at " + get_local_time().strftime('%Y/%m/%d %I:%M:%S %p'))
        command = next_color.apply_to_command({'transitiontime': 60 * 10})  # 60 s transition
        command_all_lights(command)
