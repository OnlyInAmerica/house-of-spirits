import time

from support.color import get_next_circadian_color
from support.hue import command_all_lights
from support.logger import get_logger
from support.time_utils import get_local_time

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
        command_all_lights(command)
