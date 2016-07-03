import time

import RPi.GPIO as GPIO
import settings

from support.logger import get_logger
from support.room import PIN_NO_PIN, PIN_EXTERNAL_SENSOR
from support.time_utils import get_local_time

# Logging
logger = get_logger("motion")

# Motion sensor pin -> Room
PIN_TO_ROOM = {}
EXTERNAL_SENSOR_ROOMS = []

# Room id
ROOM_NAME_TO_IDX = {}

for idx, room in enumerate(settings.ROOMS):
    ROOM_NAME_TO_IDX[room.name] = idx

    pin = room.motion_pin
    if pin == PIN_EXTERNAL_SENSOR:
        EXTERNAL_SENSOR_ROOMS.append(room)
    elif pin != PIN_NO_PIN:
        PIN_TO_ROOM[room.motion_pin] = room


def on_motion(triggered_pin: int):
    now = get_local_time()

    is_motion_start = GPIO.input(triggered_pin)

    room = PIN_TO_ROOM[triggered_pin]
    logger.info("Motion %s in %s" %
                (("started" if is_motion_start else "stopped"), room.name))

    # Ignore repeat motion stop events
    if not is_motion_start and not room.motion_started:
        return

    room.on_motion(now, is_motion_start=is_motion_start)

    neighbor_room_names = settings.ROOM_GRAPH.get(room.name, None)
    if neighbor_room_names is not None:
        logger.info("Notifying %s neighbors (%s) of motion" % (room.name, neighbor_room_names))
        for neighbor_room_name in neighbor_room_names:
            neighbor_room = settings.ROOMS[ROOM_NAME_TO_IDX[neighbor_room_name]]
            neighbor_room.on_neighbor_motion(now, is_motion_start=is_motion_start)


def disable_inactive_lights():
    now_date = get_local_time()
    logger.info("begin disable_inactive_lights")
    motion_rooms = list(PIN_TO_ROOM.values())
    motion_rooms += EXTERNAL_SENSOR_ROOMS

    for room in motion_rooms:

        inactive = room.is_motion_timed_out(as_of_date=now_date)
        logger.info("room %s is timed out %r" % (room.name, inactive))

        if not inactive:
            continue

        room.switch(on=False)



try:
    # RPi GPIO
    GPIO.setmode(GPIO.BCM)

    for active_pin in PIN_TO_ROOM.keys():
        GPIO.setup(active_pin, GPIO.IN)
        GPIO.add_event_detect(active_pin, GPIO.BOTH, callback=on_motion)

    min_motion_timeout_room = min(settings.ROOMS, key=lambda room: room.motion_timeout)
    min_motion_timeout = min_motion_timeout_room.motion_timeout
    logger.info("Min motion timeout %s", str(min_motion_timeout))

    while 1:
        time.sleep(float(min_motion_timeout.seconds) / 2)
        disable_inactive_lights()


except KeyboardInterrupt:
    print("Adios!")
    GPIO.cleanup()
