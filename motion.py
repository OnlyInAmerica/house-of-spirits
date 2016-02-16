import datetime
import time

import RPi.GPIO as GPIO

from support.color import add_circadian_hue_to_command
from support.hue import hue
from support.logger import get_logger
from support.room import Room, ROOMS
from support.time_utils import get_local_sunset, get_local_sunrise, get_local_time

# Logging
logger = get_logger("motion")

# Configuration

MOTION_DIM_TIMEOUT = datetime.timedelta(minutes=10)
MOTION_OFF_TIMEOUT = datetime.timedelta(minutes=16)

PIN_LIVING_ROOM = 4
# TODO : Following pins are not yet assigned
PIN_BEDROOM = 5
PIN_KITCHEN = 6
PIN_HALLWAY = 7
PIN_STAIRWAY = 8

PIR_PINS = [PIN_LIVING_ROOM]

PIN_TO_ROOM_MAP = {
    PIN_LIVING_ROOM: ROOMS["Living Room"],
    PIN_KITCHEN: ROOMS["Kitchen"],
    PIN_BEDROOM: ROOMS["Bedroom"],
    PIN_STAIRWAY: ROOMS["Stairway"],
    PIN_HALLWAY: ROOMS["Hallway"]
}

# Pin -> RoomLights
PIN_TO_ROOM_LIGHTS = {}

# RPi GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_LIVING_ROOM, GPIO.IN)


class RoomLights:
    def __init__(self, room: Room, last_motion: datetime = get_local_time()):
        self.room = room
        self.dimmed = False
        self.last_motion = last_motion
        self.motion_started = False  # Keep track of started to ignore spurious stop events

    def switch(self, on: bool):

        # Ignore requests that won't change state
        if hue.get_light(self.room.lights[0], 'on') == on:
            return

        self.dimmed = False
        if on:
            command = {'on': True, 'bri': 254}
        else:
            command = {'on': False}

        logger.info("Powering " + ("on" if on else "off") + " " + self.room.name + " lights.")
        self.update(command)

    def dim(self, brightness: float = .5, transitiontime_s=5):
        if self.dimmed:
            return

        self.dimmed = True
        logger.info("Dimming " + self.room.name + " lights.")
        self.update({
            'transitiontime': transitiontime_s * 10,  # Hue API uses deciseconds
            'on': True,
            'bri': int(min(254, 254 * brightness))
        })

    def update(self, command: dict):
        for light in self.room.lights:
            hue.set_light(light, add_circadian_hue_to_command(command))


def on_motion(triggered_pin: int):
    motion_start = GPIO.input(triggered_pin)

    room = PIN_TO_ROOM_MAP[pin]

    # Ignore repeat motion stop events
    if not motion_start and not room.motion_started:
        return
    room.motion_started = motion_start

    now = get_local_time()

    sunrise = get_local_sunrise() + datetime.timedelta(minutes=120)
    sunset = get_local_sunset() - datetime.timedelta(minutes=30)

    message = room.name + " motion " + ("started" if motion_start else "stopped")
    logger.info(message)

    if triggered_pin not in PIN_TO_ROOM_LIGHTS:
        PIN_TO_ROOM_LIGHTS[triggered_pin] = RoomLights(room=room, last_motion=now)

    lights = PIN_TO_ROOM_LIGHTS[triggered_pin]

    if motion_start and (now > sunset or now < sunrise):
        lights.switch(True)


def disable_inactive_lights():
    now_date = get_local_time()
    for pin, lights in PIN_TO_ROOM_LIGHTS.items():
        since_motion = now_date - lights.last_motion
        if since_motion > MOTION_OFF_TIMEOUT:
            lights.switch(on=False)
        elif since_motion > MOTION_DIM_TIMEOUT:
            lights.dim()


try:
    for pin in PIR_PINS:
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=on_motion)

    while 1:
        time.sleep(float(MOTION_DIM_TIMEOUT.seconds / 2))  # Should take into account (Off - dim) timeouts
        disable_inactive_lights()


except KeyboardInterrupt:
    print("Adios!")
    GPIO.cleanup()
