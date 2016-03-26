import datetime

import copy

from support.color import adjust_command_for_time, get_current_circadian_color
from support.hue import hue, COMMAND_FULL_ON, COMMAND_OFF
from support.logger import get_logger

logger = get_logger("rooms")

PIN_NO_PIN = -1


class Room:
    def __init__(self,
                 name: str,
                 lights: [int],
                 motion_pin: int = PIN_NO_PIN,
                 motion_timeout: datetime = datetime.timedelta(minutes=20)):
        """
        :param name: the human-readable room name
        :param lights: the Hue API Ids of contained lights
        :param motion_pin: the Raspberry Pi GPIO pin number
        :param motion_timeout: After no motion within this period, room will be darkened
        """
        self.name = name
        self.lights = lights
        self.motion_pin = motion_pin
        self.motion_timeout = motion_timeout

        self.motion_started = False
        self.last_motion = None

    def on_motion(self, motion_datetime: datetime, is_motion_start: bool = True):
        self.last_motion = motion_datetime
        self.motion_started = is_motion_start

        circadian_color = get_current_circadian_color(date=motion_datetime)

        if is_motion_start and circadian_color.brightness > 0:
            self.switch(True, adjust_hue_for_time=False, extra_command=circadian_color.apply_to_command({}))

    def is_motion_timed_out(self, as_of_date: datetime) -> bool:
        if self.last_motion is None:
            return False  # Don't consider a room that never saw motion as timed out

        since_motion = as_of_date - self.last_motion
        return since_motion > self.motion_timeout

    def switch(self, on: bool, adjust_hue_for_time: bool=True, extra_command: dict = None):

        # Ignore requests that won't change state
        if hue.get_light(self.lights[0], 'on') == on:
            return

        command = copy.deepcopy(COMMAND_FULL_ON if on else COMMAND_OFF)  # Don't alter reference command
        if extra_command is not None:
            command.update(extra_command)

        if adjust_hue_for_time:
            command = adjust_command_for_time(command)

        logger.info("Powering " + ("on" if on else "off") + " " + self.name + " lights.")

        self.update(command)

    def dim(self, brightness: float = .5, transitiontime_s: int=5):

        logger.info("Dimming " + self.name + " lights.")
        self.update({
            'transitiontime': transitiontime_s * 10,  # Hue API uses deciseconds
            'on': True,
            'bri': int(min(254, 254 * brightness))
        })

    def update(self, command: dict):
        logger.info("Sending %s to %s", str(command), self.name)
        result = hue.set_light(self.lights, command)
        logger.info("Update result %s", str(result))

    def is_lit(self):
        for light in self.lights:
            if hue.get_light(light, 'on'):
                return True
        return False
