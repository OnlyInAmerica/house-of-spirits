import datetime
import json

import copy

from support.color import adjust_command_for_time
from support.hue import hue, COMMAND_FULL_ON, COMMAND_OFF

from support.logger import get_logger
from support.time_utils import get_local_sunrise, get_local_sunset
from weather import FORECAST_FILENAME

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

        sunrise = get_local_sunrise() + datetime.timedelta(minutes=150)
        sunset = get_local_sunset() - datetime.timedelta(minutes=60)

        try:
            forecast_file = open(FORECAST_FILENAME, 'r')
            forecast = json.loads(forecast_file.read())
            forecast_file.close()
            cloud_cover = forecast["cloud_cover"]
        except FileNotFoundError:
            cloud_cover = 0

        if is_motion_start and cloud_cover > .5 or (motion_datetime > sunset or motion_datetime < sunrise):
            self.switch(True)

    def is_motion_timed_out(self, as_of_date: datetime) -> bool:
        if self.last_motion is None:
            return False  # Don't consider a room that never saw motion as timed out

        since_motion = as_of_date - self.last_motion
        return since_motion > self.motion_timeout

    def switch(self, on: bool, adjust_hue_for_time=True):

        # Ignore requests that won't change state
        if hue.get_light(self.lights[0], 'on') == on:
            return

        command = COMMAND_FULL_ON if on else COMMAND_OFF
        command = copy.deepcopy(command)  # Don't alter reference command

        logger.info("Powering " + ("on" if on else "off") + " " + self.name + " lights.")

        adjusted_command = adjust_command_for_time(command)
        self.update(adjusted_command)

    def dim(self, brightness: float = .5, transitiontime_s=5):

        logger.info("Dimming " + self.name + " lights.")
        self.update({
            'transitiontime': transitiontime_s * 10,  # Hue API uses deciseconds
            'on': True,
            'bri': int(min(254, 254 * brightness))
        })

    def update(self, command: dict):
        logger.info("Sending %s to %s", str(command), self.name)
        for light in self.lights:
            hue.set_light(light, command)
