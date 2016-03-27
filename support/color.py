import datetime

import copy

from support.hue import COMMAND_OFF
from support.logger import get_logger
from support.time_utils import get_local_sunrise, get_local_sunset, get_local_dusk, get_local_dawn, \
    LOCAL_TIMEZONE
from support.weather_utils import is_cloudy

LIGHT_DAYTIME_XY = [0.4506, 0.4081]
LIGHT_EVENING_XY = [0.4904, 0.4075]
LIGHT_NIGHT_XY = [0.5304, 0.4068]
LIGHT_LATENIGHT_XY = [0.6185, 0.363]

logger = get_logger("color")


class CircadianColor:
    def __init__(self, name: str, color_xy: list, brightness: int, trigger_date_function: callable):
        """
        A light setting that depends only on the circadian cycle.

        :param name: human-readable name
        :param color_xy: the hue accompanying this circadian event. See http://www.developers.meethue.com/documentation/hue-xy-values
        :param brightness: the brightness from 0 to 255. If zero, will be treated as switch-off command
        :param trigger_date_function: a function returning the start time for the day the function is called.
        :return:
        """
        self.name = name
        self.color_xy = color_xy
        self.brightness = brightness
        self.trigger_date_function = trigger_date_function

    def is_valid_for_date(self, date: datetime):
        """
        :return: whether this color is in effect on the given date
        """
        return True

    def apply_to_command(self, command: dict) -> dict:
        # Cannot set properties if power off
        if self.brightness == 0:
            return copy.deepcopy(COMMAND_OFF)

        command['xy'] = copy.deepcopy(self.color_xy)  # Don't allow client to modify self.color_xy
        command['bri'] = self.brightness
        return command


class SunnyPlusCircadianColor(CircadianColor):
    """
    A light setting that depends on sunny weather and the circadian cycle.
    """

    def is_valid_for_date(self, date: datetime):
        return not is_cloudy()


# The pairs here should be in-order so that the next circadian event can be found by iterating through until
# trigger_date_function returns a date before the current date
CIRCADIAN_COLORS_ASC = [

    CircadianColor(name='Night',
                   color_xy=[0.6185, 0.363],
                   brightness=100,
                   trigger_date_function=lambda date: date.replace(hour=0, minute=0, second=0, microsecond=0)),  # Midnight of this day

    CircadianColor(name='Dawn',
                   color_xy=[0.5304, 0.4068],
                   brightness=100,
                   trigger_date_function=lambda date: get_local_dawn(date) - datetime.timedelta(hours=1)),

    CircadianColor(name='Sunrise',
                   color_xy=[0.4506, 0.4081],
                   brightness=255,
                   trigger_date_function=lambda date: get_local_sunrise(date)),

    SunnyPlusCircadianColor(name='Day',
                            color_xy=[0, 0],
                            brightness=0,
                            trigger_date_function=lambda date: get_local_sunrise(
                                date) + datetime.timedelta(minutes=200)),

    CircadianColor(name='Sunset',
                   color_xy=[0.4904, 0.4075],
                   brightness=255,
                   trigger_date_function=lambda date: get_local_sunset(date) - datetime.timedelta(hours=1)),

    CircadianColor(name='Dusk',
                   color_xy=[0.5304, 0.4068],
                   brightness=255,
                   trigger_date_function=lambda date: get_local_dusk(date) + datetime.timedelta(hours=2))
]


def get_next_circadian_color(date: datetime = None) -> (datetime, CircadianColor):
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    current_color = get_current_circadian_color(date)
    current_color_idx = CIRCADIAN_COLORS_ASC.index(current_color)

    while True:

        if current_color_idx == len(CIRCADIAN_COLORS_ASC) - 1:
            current_color_idx = 0
            next_color = CIRCADIAN_COLORS_ASC[current_color_idx]
            next_date = next_color.trigger_date_function(date + datetime.timedelta(days=1))  # First event tomorrow
        else:
            current_color_idx += 1
            next_color = CIRCADIAN_COLORS_ASC[current_color_idx]
            next_date = next_color.trigger_date_function(date)

        logger.info("Testing next event (%s) after %s", next_color.name, current_color.name)

        if next_color.is_valid_for_date(date):
            break

    logger.info("Next event after %s is %s at %s",
                date.strftime('%Y/%m/%d %I:%M:%S %p'),
                next_color.name,
                next_date.strftime('%Y/%m/%d %I:%M:%S %p'))

    return next_date, next_color


def get_current_circadian_color(date: datetime = None) -> CircadianColor:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    current_color = None

    for color in reversed(CIRCADIAN_COLORS_ASC):
        if color.trigger_date_function(date) < date and color.is_valid_for_date(date):
            current_color = color
            break

    # Note this won't happen so long as first color occurs at midnight
    if current_color is None:
        current_color = CIRCADIAN_COLORS_ASC[-1]

    logger.info("Current event at %s is %s since %s",
                date.strftime('%Y/%m/%d %I:%M:%S %p'),
                current_color.name,
                current_color.trigger_date_function(date).strftime('%Y/%m/%d %I:%M:%S %p'))

    return current_color


def adjust_command_for_time(command: dict) -> dict:
    # Cannot set xy property if power off
    if 'on' in command and command['on'] is False:
        return command

    circadian_color = get_current_circadian_color()
    circadian_color.apply_to_command(command)

    return command
