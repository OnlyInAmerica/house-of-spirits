import datetime
import threading
import time

import RPi.GPIO as GPIO
import settings

from support.env import set_motion_enabled, is_motion_enabled, set_room_occupied, get_room_occupied
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

OCCUPIED_ROOMS = set([])  # Rooms with motion and no exit events
EXITED_ROOMS = set([])  # Rooms where an exit event occurred

# Even an allegedly occupied room should be shut off after no motion for this period
OCCUPIED_ROOM_MOTION_TIMEOUT = datetime.timedelta(hours=2)

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

    exit_src_room_last_motion = exit_src_room.get_last_motion()
    exit_dst_room_last_motion = exit_dst_room.get_last_motion()
    # Is the exit src room still in motion (start but no stop event) or has exit src room motion ended
    # within a very short period of the exit_dst_room
    result = exit_src_room_last_motion is not None and exit_dst_room_last_motion is not None \
           and (exit_src_room.motion_started or
                exit_dst_room_last_motion - exit_src_room_last_motion < datetime.timedelta(seconds=20))

    if not result:
        reason = ""
        if not (exit_src_room_last_motion is not None):
            reason += "%s has no last motion. " % exit_src_room
        if not (exit_dst_room_last_motion is not None):
            reason += "%s has no last motion. " % exit_dst_room
        if not (exit_src_room.motion_started):
            reason += "%s motion has not started. " % exit_src_room
        if (exit_src_room_last_motion is not None and exit_dst_room_last_motion is not None) and not (exit_dst_room_last_motion - exit_src_room_last_motion < datetime.timedelta(seconds=10)):
            reason += "Difference between dst (%s) and src (%s) motion is only %s" % (exit_dst_room.name, exit_src_room.name, exit_dst_room_last_motion - exit_src_room_last_motion)
        logger.info("Motion from %s does not corroborate exit from %s because %s" % (exit_dst_room, exit_src_room, reason))

    return result

def on_gpio_motion(triggered_pin: int):
    # TODO : Currently motion pins are used as zigbee addresses
    room = PIN_TO_ROOM[triggered_pin]
    is_motion_start = GPIO.input(triggered_pin)
    on_motion(room, is_motion_start)

def on_motion(room: Room, is_motion_start: bool):
    now = get_local_time()

    logger.info("Motion %s in %s" %
                (("started" if is_motion_start else "stopped"), room.name))

    # Ignore event if motion disabled
    if not is_motion_enabled():
        logger.info("Motion disabled. Ignoring event")
        return

    # Ignore repeat motion stop events
    if not is_motion_start and not room.motion_started:
        return

    room.on_motion(now, is_motion_start=is_motion_start)

    if is_motion_start:
        OCCUPIED_ROOMS.add(room)
        EXITED_ROOMS.discard(room)
        set_room_occupied(room.name, True)

        exit_src_rooms = EXIT_ROOM_NAME_TO_SOURCE_ROOM_NAMES.get(room.name, None)
        if is_motion_start and exit_src_rooms is not None:
            exit_dst_room = room
            # logger.info("Notifying %s of possible exit to %s" % (exit_src_rooms, exit_dst_room.name))
            for exit_src_room_name in exit_src_rooms:
                exit_src_room = settings.ROOMS[ROOM_NAME_TO_IDX[exit_src_room_name]]
                if exit_src_room in OCCUPIED_ROOMS and corroborates_exit(exit_dst_room, exit_src_room):
                    logger.info("%s motion corroborates exit from %s" % (exit_dst_room, exit_src_room))
                    EXITED_ROOMS.add(exit_src_room)
                    OCCUPIED_ROOMS.discard(exit_src_room)
                    set_room_occupied(room.name, False)
        logger.info("Occupied rooms %s" % OCCUPIED_ROOMS)


def disable_inactive_lights():
    now_date = get_local_time()
    motion_rooms = list(PIN_TO_ROOM.values())
    motion_rooms += EXTERNAL_SENSOR_ROOMS

    log_msg = "Disable inactive lights report: "

    for room in motion_rooms:

        inactive = room.is_motion_timed_out(as_of_date=now_date)
        log_msg += "%s is %s. " % (room.name, "inactive" if inactive else "active")

        if not inactive:
            continue

        # An 'occupied' room has a higher motion timeout. This combats events we can't control.
        # e.g: A flash of light through a window or a neighboring room's lighting triggering motion
        since_motion = now_date - room.get_last_motion()
        occupied_timed_out = since_motion > OCCUPIED_ROOM_MOTION_TIMEOUT

        if inactive and room.name in settings.ROOM_GRAPH:
            if room in EXITED_ROOMS:
                log_msg += "Inactive Room %s has an exit event. Power off. " % room.name
            elif occupied_timed_out:
                log_msg += "Inactive Room %s has no exit event but is motionless beyond occupied timeout. Power off. " % room.name
            else:
                log_msg += "Inactive Room %s has no exit event. Keep on. " % room.name
                continue
        else:
            log_msg += "Inactive Room %s has no exit dst neighbors. Power off. " % room.name

        room.switch(on=False)

        # Never consider a powered-off room as occupied
        OCCUPIED_ROOMS.discard(room)
        set_room_occupied(room.name, False)
    log_msg += "Occupied rooms %s" % OCCUPIED_ROOMS
    logger.info(log_msg)

def monitor_zigbee():
    import re
    import socket
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5005  # Ugh can't import from python3 land
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP
    sock.bind((UDP_IP, UDP_PORT))

    regexp = re.compile(r'^([a-z]+)-(\d+)-(.+)')
    while 1:
        data, addr = sock.recvfrom(255)
        m = regexp.match(data.decode('utf-8'))
        if m:
            type = m.group(1)
            addr = int(m.group(2))
            val = m.group(3)
            if addr in PIN_TO_ROOM:
                room = PIN_TO_ROOM[addr]
                if type == 'motion':
                    is_motion_start = int(val) == 1
                    logger.info("Got zigbee %s for room %s with value %s",
                                type, room, val)
                    on_motion(room, is_motion_start)
                elif type == 'luminance':
                    luminance_lux = float(val)
                    room.luminance_lux = luminance_lux
                elif type == 'temp':
                    temp_fahrenheit = float(val)
                    room.temp_fahrenheit = temp_fahrenheit
                else:
                    logger.warn("Got zigbee command with unknown type %s", m.group(0))
            else:
                logger.warn("Got zigbee command from unknown addr %l", addr)
        else:
            logger.info("Got unrecognized zigbee socket data %s", data)

try:
    # RPi GPIO
    '''
    GPIO.setmode(GPIO.BCM)

    for active_pin in PIN_TO_ROOM.keys():
        GPIO.setup(active_pin, GPIO.IN)
        GPIO.add_event_detect(active_pin, GPIO.BOTH, callback=on_gpio_motion)
    '''

    zb = threading.Thread(target=monitor_zigbee)
    zb.start()

    min_motion_timeout_room = min(settings.ROOMS, key=lambda room: room.motion_timeout)
    min_motion_timeout = min_motion_timeout_room.motion_timeout
    logger.info("Min motion timeout %s", str(min_motion_timeout))

    # When the motion process starts, set motion enabled
    set_motion_enabled(True)

    while 1:
        time.sleep(float(min_motion_timeout.seconds) / 2)
        if is_motion_enabled():
            disable_inactive_lights()


except KeyboardInterrupt:
    GPIO.cleanup()
