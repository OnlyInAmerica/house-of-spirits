import time

import RPi.GPIO as GPIO
import settings

from support.logger import get_logger
from support.room import PIN_NO_PIN
from support.time_utils import get_local_time

# Logging
logger = get_logger("motion")

# Motion sensor pin -> Room
PIN_TO_ROOM = {}

for room in settings.ROOMS:
    pin = room.motion_pin
    if pin != PIN_NO_PIN:
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


def disable_inactive_lights():
    now_date = get_local_time()
    logger.info("begin disable_inactive_lights")
    for pin, room in PIN_TO_ROOM.items():

        inactive = room.is_motion_timed_out(as_of_date=now_date)
        logger.info("room %s is timed out %r" % (room.name, inactive))

        if not inactive:
            continue

        # Motion must have occurred in neighbor room afterward for this room to be inactive
        neighbor_room_names = settings.ROOM_GRAPH.get(room.name, None)
        if neighbor_room_names is not None:
            logger.info("evaluating neighbors (%s) for %s" % (neighbor_room_names, room.name))
            subsequent_neighbor_motion = False
            for neighbor_room_name in neighbor_room_names:
                for pot_neighbor_room in settings.ROOMS:
                    logger.info("evaluating potential neighbor (%s) for name %s" % (pot_neighbor_room.name, neighbor_room_name))
                    if neighbor_room_name == pot_neighbor_room.name:
                        neighbor_corroborates_exit = pot_neighbor_room.last_motion is not None and pot_neighbor_room.last_motion > room.last_motion
                        logger.info("evaluating room %s neighbor %s. Neighbor moved after this %r" % (room.name, neighbor_room_name, neighbor_corroborates_exit))
                        if neighbor_corroborates_exit:
                            subsequent_neighbor_motion = True
                            break

            if not subsequent_neighbor_motion:
                logger.info("Room %s is timed out but neighbors (%s) have not received motion afterward, "
                            "so room must still be occupied." % (room.name, neighbor_room_names))
                continue

        room.switch(on=False)
    logger.info("end disable_inactive_lights")



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
