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

DEFAULT_MOTION_TIMEOUT = datetime.timedelta(minutes=20)

PIN_LIVING_ROOM = 17
PIN_HALLWAY = 27
PIN_KITCHEN = 4
# TODO : Following pins are not yet assigned
PIN_BEDROOM = 5
PIN_STAIRWAY = 8

ACTIVE_PIR_PINS = [PIN_LIVING_ROOM, PIN_KITCHEN, PIN_HALLWAY]

# RPi GPIO
GPIO.setmode(GPIO.BCM)
for active_pin in ACTIVE_PIR_PINS:
    GPIO.setup(active_pin, GPIO.IN)


class RoomLights:
    def __init__(self, room: Room,
                 last_motion: datetime = get_local_time(),
                 motion_timeout: datetime.timedelta = DEFAULT_MOTION_TIMEOUT):
        self.room = room
        self.last_motion = last_motion
        self.motion_started = False  # Keep track of started to ignore spurious stop events
        self.motion_timeout = motion_timeout

    def switch(self, on: bool):

        # Ignore requests that won't change state
        if hue.get_light(self.room.lights[0], 'on') == on:
            return

        if on:
            command = {'on': True, 'bri': 254}
        else:
            command = {'on': False}

        logger.info("Powering " + ("on" if on else "off") + " " + self.room.name + " lights.")
        self.update(command)

    def dim(self, brightness: float = .5, transitiontime_s=5):

        logger.info("Dimming " + self.room.name + " lights.")
        self.update({
            'transitiontime': transitiontime_s * 10,  # Hue API uses deciseconds
            'on': True,
            'bri': int(min(254, 254 * brightness))
        })

    def update(self, command: dict):
        adjusted_command = add_circadian_hue_to_command(command)
        logger.info("Sending %s to %s", str(adjusted_command), self.room.name)
        for light in self.room.lights:
            hue.set_light(light, adjusted_command)


PIN_TO_ROOM_LIGHTS = {
    PIN_LIVING_ROOM: RoomLights(room=ROOMS["Living Room"], motion_timeout=datetime.timedelta(hours=1)),
    PIN_KITCHEN: RoomLights(room=ROOMS["Kitchen"], motion_timeout=datetime.timedelta(minutes=15)),
    PIN_BEDROOM: RoomLights(room=ROOMS["Bedroom"]),
    PIN_STAIRWAY: RoomLights(room=ROOMS["Stairway"]),
    PIN_HALLWAY: RoomLights(room=ROOMS["Hallway"], motion_timeout=datetime.timedelta(minutes=5))
}


def on_motion(triggered_pin: int):
    now = get_local_time()

    is_motion_start = GPIO.input(triggered_pin)

    lights = PIN_TO_ROOM_LIGHTS[triggered_pin]

    # Ignore repeat motion stop events
    if not is_motion_start and not lights.motion_started:
        return
    lights.motion_started = is_motion_start
    lights.last_motion = now

    sunrise = get_local_sunrise() + datetime.timedelta(minutes=150)
    sunset = get_local_sunset() - datetime.timedelta(minutes=50)

    message = lights.room.name + " motion " + ("started" if is_motion_start else "stopped")
    logger.info(message)

    if is_motion_start and (now > sunset or now < sunrise):
        lights.switch(True)


def disable_inactive_lights():
    now_date = get_local_time()
    for pin, lights in PIN_TO_ROOM_LIGHTS.items():
        if pin not in ACTIVE_PIR_PINS:
            continue

        since_motion = now_date - lights.last_motion
        if since_motion > lights.motion_timeout:
            lights.switch(on=False)

try:
    for pin in ACTIVE_PIR_PINS:
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=on_motion)

    min_motion_timeout_room = min(PIN_TO_ROOM_LIGHTS.values(), key=lambda x: x.motion_timeout)
    min_motion_timeout = min_motion_timeout_room.motion_timeout
    logger.info("Min motion timeout %s", str(min_motion_timeout))

    while 1:
        time.sleep(float(min_motion_timeout.seconds) / 2)
        disable_inactive_lights()


except KeyboardInterrupt:
    print("Adios!")
    GPIO.cleanup()
