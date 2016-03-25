import datetime

import copy

from support.logger import get_logger
from support.time_utils import get_local_sunrise, get_local_sunset, get_local_time, get_local_dusk, get_local_dawn, \
    LOCAL_TIMEZONE

LIGHT_DAYTIME_XY = [0.4506, 0.4081]
LIGHT_EVENING_XY = [0.4904, 0.4075]
LIGHT_NIGHT_XY = [0.5304, 0.4068]
LIGHT_LATENIGHT_XY = [0.6185, 0.363]

logger = get_logger("color")


class CircadianColor:
    def __init__(self, name: str, color_xy: list, brightness: int, trigger_date_function: callable):
        """

        :param name: human-readable name
        :param color_xy: the hue accompanying this circadian event. See http://www.developers.meethue.com/documentation/hue-xy-values
        :param brightness: the brightness from 0 to 255
        :param trigger_date_function: a function returning the start time for the day the function is called.
        :return:
        """
        self.name = name
        self.color_xy = color_xy
        self.brightness = brightness
        self.trigger_date_function = trigger_date_function

    def apply_to_command(self, command: dict):
        command['xy'] = copy.deepcopy(self.color_xy)  # Don't allow client to modify self.color_xy
        command['brightness'] = self.brightness


# The pairs here should be in-order so that the next circadian event can be found by iterating through until
# trigger_date_function returns a date before the current date
CIRCADIAN_COLORS_ASC = [

    CircadianColor(name='Night',
                   color_xy=[0.6185, 0.363],
                   brightness=100,
                   trigger_date_function=lambda: get_local_time().replace(hour=5, minute=0)),
    CircadianColor(name='Dawn',
                   color_xy=[0.5304, 0.4068],
                   brightness=200,
                   trigger_date_function=lambda: get_local_dawn() - datetime.timedelta(hours=1)),

    CircadianColor(name='Day',
                   color_xy=[0.4506, 0.4081],
                   brightness=255,
                   trigger_date_function=lambda: get_local_sunrise()),

    CircadianColor(name='Sunset',
                   color_xy=[0.4904, 0.4075],
                   brightness=255,
                   trigger_date_function=lambda: get_local_sunset()),

    CircadianColor(name='Evening',
                   color_xy=[0.5304, 0.4068],
                   brightness=255,
                   trigger_date_function=lambda: get_local_dusk() + datetime.timedelta(hours=2))
]


def get_next_circadian_color(date: datetime = None) -> CircadianColor:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    for color in CIRCADIAN_COLORS_ASC:
        trigger_date = color.trigger_date_function()
        if date < trigger_date:
            return color

    return CIRCADIAN_COLORS_ASC[-1]


def get_current_circadian_color(date: datetime = None) -> CircadianColor:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    for color in reversed(CIRCADIAN_COLORS_ASC):
        trigger_date = color.trigger_date_function()
        if date > trigger_date:
            return color

    return CIRCADIAN_COLORS_ASC[0]


def adjust_command_for_time(command: dict) -> dict:
    # Cannot set xy property if power off
    if 'on' in command and command['on'] is False:
        return command

    circadian_color = get_current_circadian_color()
    circadian_color.apply_to_command(command)

    return command
