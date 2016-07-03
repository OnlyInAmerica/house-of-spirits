import datetime

import copy

from support import env
from support.color import adjust_command_for_time, get_current_circadian_color
from support.hue import hue, COMMAND_FULL_ON, COMMAND_OFF
from support.logger import get_logger

logger = get_logger("rooms")

PIN_NO_PIN = -1  # For rooms without motion capabilities
PIN_EXTERNAL_SENSOR = -2  # For rooms with motion sensed externally. Use env.get_room_last_motion_date to check state


class Room:
    def __init__(self,
                 name: str,
                 lights: [int],
                 motion_pin: int = PIN_NO_PIN,
                 motion_timeout: datetime = datetime.timedelta(minutes=20),
                 has_motion_neighbors: bool=False):
        """
        :param name: the human-readable room name
        :param lights: the Hue API Ids of contained lights
        :param motion_pin: the Raspberry Pi GPIO pin number
        :param motion_timeout: After no motion within this period, room will be darkened
        :param has_motion_neighbors: Whether this room has motion-sensing neighbors used to determine is_motion_timed_out
        """
        self.name = name
        self.lights = lights
        self.motion_pin = motion_pin
        self.motion_timeout = motion_timeout
        self.has_motion_neighbors = has_motion_neighbors

        self.motion_started = False
        self.last_motion = None
        self.first_subsequent_neighbor_motion = None  # First neighbor motion ocurring after last_motion

    def on_motion(self, motion_datetime: datetime, is_motion_start: bool = True):

        # Ignore motion events in party mode
        if env.is_party_mode():
            return

        self.first_subsequent_neighbor_motion = None
        self.last_motion = motion_datetime
        self.motion_started = is_motion_start

        circadian_color = get_current_circadian_color(date=motion_datetime)

        if is_motion_start and circadian_color.brightness > 0:
            self.switch(True, adjust_hue_for_time=False, extra_command=circadian_color.apply_to_command({}))

    def on_neighbor_motion(self, motion_datetime: datetime, is_motion_start: bool = True):
        if is_motion_start and self.first_subsequent_neighbor_motion is None:
            self.first_subsequent_neighbor_motion = motion_datetime

    def is_motion_timed_out(self, as_of_date: datetime) -> bool:
        if self.motion_pin == PIN_EXTERNAL_SENSOR:
            self.last_motion = env.get_room_last_motion_date(self.name)

        # Don't consider a room that never saw motion as timed out
        if self.last_motion is None:
            return False

        # Lights cannot time out in party mode
        if env.is_party_mode():
            return False

        since_motion = as_of_date - self.last_motion
        timed_out = since_motion > self.motion_timeout

        if timed_out and self.has_motion_neighbors and self.first_subsequent_neighbor_motion is not None:
            timed_out = self.first_subsequent_neighbor_motion - self.last_motion < datetime.timedelta(seconds=5)
            logger.info("Room %s is timed out. First subsequent neighbor motion is %s. Timed out %r" %
                        (self.name, self.first_subsequent_neighbor_motion.strftime('%Y/%m/%d %I:%M:%S %p'), timed_out))

        return timed_out

    def switch(self, on: bool, adjust_hue_for_time: bool=True, extra_command: dict = None):

        # Ignore requests that won't change state
        if self.is_lit() == on:
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


class LightsOnDuringDayRoom(Room):
    """
    A Room that interprets the lights-off 'Day' CircadianColor with full brightness lighting
    """

    def on_motion(self, motion_datetime: datetime, is_motion_start: bool = True):
        self.last_motion = motion_datetime
        self.motion_started = is_motion_start

        circadian_color = get_current_circadian_color(date=motion_datetime)
        if is_motion_start:
            command = circadian_color.apply_to_command({})
            if circadian_color.name == 'Day':
                command['on'] = True
                command['bri'] = 255
                command['xy'] = circadian_color.color_xy

            self.switch(True, adjust_hue_for_time=False, extra_command=command)


class GuestModeRoom(Room):
    """
    A Room that does not switch lights in response to motion while in Guest Mode.
    """

    def on_motion(self, motion_datetime: datetime, is_motion_start: bool = True):
        logger.info("GuestModeRoom on_motion. Guest mode %s", str(env.is_guest_mode()))
        if not env.is_guest_mode():
            super(GuestModeRoom, self).on_motion(motion_datetime=motion_datetime,
                                                 is_motion_start=is_motion_start)

    def is_motion_timed_out(self, as_of_date: datetime) -> bool:
        if not env.is_guest_mode():
            return super(GuestModeRoom, self).is_motion_timed_out(as_of_date=as_of_date)
        return False
