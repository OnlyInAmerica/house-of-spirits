import datetime
import time

import RPi.GPIO as GPIO
import settings

from support.logger import get_logger
from support.room import PIN_NO_PIN, PIN_EXTERNAL_SENSOR, Room
from support.time_utils import get_local_time

# Logging
logger = get_logger("motion")

# Motion sensor pin -> Room
PIN_TO_ROOM = {}
EXTERNAL_SENSOR_ROOMS = []

# Room id
ROOM_NAME_TO_IDX = {}

# Neighbors to notify
EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES = {}

# TODO : Need to share collection of occupied rooms so circadian can effect them...
OCCUPIED_ROOMS = []  # Rooms with motion and no exit events
EXITED_ROOMS = []  # Rooms where an exit event occurred

for idx, room in enumerate(settings.ROOMS):
    ROOM_NAME_TO_IDX[room.name] = idx

    if room.name in settings.ROOM_GRAPH:
        exit_room_names = settings.ROOM_GRAPH[room.name]
        for exit_room_name in exit_room_names:
            if exit_room_name not in EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES:
                EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES[exit_room_name] = []
            # Hallway -> [Living Room, Kitchen]
            EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES[exit_room_name].append(room.name)

    pin = room.motion_pin
    if pin == PIN_EXTERNAL_SENSOR:
        EXTERNAL_SENSOR_ROOMS.append(room)
    elif pin != PIN_NO_PIN:
        PIN_TO_ROOM[room.motion_pin] = room

logger.info("Prepped exit map %s", EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES)


def corroborates_exit(exit_dst_room: Room, exit_src_room: Room):
    # Is the exit src room still in motion (start but no stop event) or has exit src room motion ended
    # within a very short period of the exit_dst_room
    return exit_src_room.last_motion is not None and exit_dst_room.last_motion is not None \
           and (exit_src_room.motion_started or
                exit_dst_room.last_motion - exit_src_room.last_motion < datetime.timedelta(seconds=5))


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

    if is_motion_start:
        logger.info("Mark %s occupied / not exited" % room.name)
        OCCUPIED_ROOMS.append(room)
        if room in EXITED_ROOMS:
            EXITED_ROOMS.remove(room)

        exit_src_rooms = EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES.get(room.name, None)
        logger.info("%s has exit sources %s" % (room.name, exit_src_rooms))
        if is_motion_start and exit_src_rooms is not None:
            exit_dst_room = room
            logger.info("Notifying %s of exit motion via %s" % (exit_src_rooms, exit_dst_room.name))
            for exit_src_room_name in exit_src_rooms:
                exit_src_room = settings.ROOMS[ROOM_NAME_TO_IDX[exit_src_room_name]]
                if corroborates_exit(exit_dst_room, exit_src_room):
                    logger.info("Mark %s is not-occupied / exited" % exit_src_room.name)
                    EXITED_ROOMS.append(exit_src_room)
                    if exit_src_room in OCCUPIED_ROOMS:
                        OCCUPIED_ROOMS.remove(exit_src_room)


def disable_inactive_lights():
    now_date = get_local_time()
    logger.info("begin disable_inactive_lights")
    motion_rooms = list(PIN_TO_ROOM.values())
    motion_rooms += EXTERNAL_SENSOR_ROOMS

    for room in motion_rooms:

        inactive = room.is_motion_timed_out(as_of_date=now_date)
        logger.info("%s is %s" % (room.name, "inactive" if inactive else "active"))

        if not inactive:
            continue

        if inactive and room.name in settings.ROOM_GRAPH:
            if room in EXITED_ROOMS:
                logger.info("Inactive Room %s has an exit event. Power off." % room.name)
            else:
                logger.info("Inactive Room %s has no exit event. Keep on" % room.name)
                continue
        else:
            logger.info("Inactive Room %s has no exit dst neighbors. Power off" % room.name)

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
