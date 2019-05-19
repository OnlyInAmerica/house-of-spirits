import datetime
import threading
import time

import RPi.GPIO as GPIO
import settings
from SECRETS import ZIGBEE_NETWORK_KEY

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
                if corroborates_exit(exit_dst_room, exit_src_room):
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
    import sys
    import signal
    from struct import *
    import argparse
    import os

    from scapy.all import *
    from killerbee import *
    from killerbee.scapy_extensions import *

    def detect_encryption(pkt):
        '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
        if not pkt.haslayer(ZigbeeSecurityHeader) or not pkt.haslayer(ZigbeeNWK):
            return False
        return True

    def detect_layer(pkt, layer):
        '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
        # if not pkt.haslayer(ZigbeeAppDataPayload):
        if not pkt.haslayer(layer):
            return False
        return True

    def interrupt(signum, frame):
        global packetcount
        global kb
        global pd, dt
        kb.sniffer_off()
        kb.close()
        if pd:
            pd.close()
        if dt:
            dt.close()

        logger.info("{0} Zigbee packets captured".format(packetcount))
        sys.exit(0)

    # Global
    packetcount = 0
    network_key = ZIGBEE_NETWORK_KEY.decode('hex')
    channel = settings.ZIGBEE_CHANNEL
    subghz_page = 0
    device = None # Auto select?

    kb = KillerBee(device=device)
    signal.signal(signal.SIGINT, interrupt)
    if not kb.is_valid_channel(channel, subghz_page):
        print >> sys.stderr, "ERROR: Must specify a valid IEEE 802.15.4 channel for the selected device."
        kb.close()
        sys.exit(1)
    kb.set_channel(channel, subghz_page)
    kb.sniffer_on()

    rf_freq_mhz = kb.frequency(channel, subghz_page) / 1000.0
    logger.info(
        "Zigbee: listening on \'{0}\', channel {1}, page {2} ({3} MHz), link-type DLT_IEEE802_15_4, capture size 127 bytes".format(
            kb.get_dev_info()[0], channel, subghz_page, rf_freq_mhz))

    # Unit conversion constants

    LUMINANCE_TO_LUX = 0.0010171925257971555

    def celsius_to_fahrenheit(celsius):
        return (celsius * 9 / 5.0) + 32

    while True:
        packet = kb.pnext()
        # packet[1] is True if CRC is correct, check removed to have promiscous capture regardless of CRC
        # if PAN filter active, only process correct PAN or ACK
        scapy_packet = None
        if packet:
            scapy_packet = Dot15d4FCS(packet['bytes'])
        if packet and panid:
            pan, layer = kbgetpanid(scapy_packet)
        if packet is not None and scapy_packet is not None and (not panid or panid == pan):  # and packet[1]:
            packetcount += 1
        # unbuffered.write("Packet " + packet['bytes'].encode('hex') + "\n")
        if detect_layer(scapy_packet, ZigbeeSecurityHeader):
            source = scapy_packet.getlayer(ZigbeeSecurityHeader).fields['source']
            if source in PIN_TO_ROOM:
                # Data from motion sensor
                room = PIN_TO_ROOM[source]
                logger.info("Event from sensor %s" % room.name)
                if detect_encryption(scapy_packet):
                    enc_data = kbdecrypt(scapy_packet, network_key)
                    # First determine if this is an occupancy sensing
                    if detect_layer(enc_data, ZigbeeAppDataPayload) and detect_layer(enc_data,
                                                                                     ZigbeeClusterLibrary):
                        app_bytes = enc_data.getlayer(ZigbeeAppDataPayload).payload.__bytes__()
                        cluster_bytes = enc_data.getlayer(ZigbeeClusterLibrary).payload.__bytes__()
                        # Occupancy Sensing
                        if app_bytes[
                           :4] == '\x06\x04\x04\x01':  # Cluster: Occupancy Sensing (0x0406), Profile: Home Automation (0x0104)
                            # print "\t"*3 + "enc cluster: " + str(cluster) + " raw: " + enc_data.getlayer(a).payload.__bytes__().encode('hex')
                            if cluster_bytes[-4:-1] == '\x00\x00\x18':  # Occupancy Sensing, 8-Bit bitmap
                                is_motion_start = cluster_bytes[-1] == '\x01'
                                on_motion(room, is_motion_start)
                            else:
                                logger.warn("Unknown Motion packet. Cluster: %s" % cluster_bytes.encode('hex'))
                        elif app_bytes[:4] == '\x00\x04\x04\x01':  # Cluster: Illuminance Measurement (0x0400), Profile: Home Automation (0x0104)
                            if cluster_bytes[-5:-2] == '\x00\x00\x21':  # Measured Value, 16-Bit Unsigned Int
                                luminance_raw = unpack('<h', cluster_bytes[-2:])[0]
                                luminance_lux = luminance_raw * LUMINANCE_TO_LUX
                                logger.info("Room %s luminance %f" % (room.name, luminance_lux))
                                room.luminance_lux = luminance_lux
                            else:
                                logger.warn("Unknown Luminance packet. Cluster: %s" % cluster_bytes.encode('hex'))
                        elif app_bytes[
                             :4] == '\x02\x04\x04\x01':  # Cluster: Temperature Measurement (0x0402), Profile: Home Automation (0x0104)
                            if cluster_bytes[-5:-2] == '\x00\x00\x29':  # Measured Value, 16-Bit Signed Int
                                temperature_raw = unpack('<h', cluster_bytes[-2:])[0]
                                temp_celsius = temperature_raw / 100.0
                                temp_fahrenheit = celsius_to_fahrenheit(temp_celsius)
                                logger.info("Room %s Temperature %f Fahrenheit" % (room.name, temp_fahrenheit))
                                room.temp_fahrenheit = temp_fahrenheit
                            else:
                                logger.warn("Unknown Temperature packet. Cluster: %s" % cluster_bytes.encode('hex'))

    kb.sniffer_off()
    kb.close()

    logger.info("{0} packets captured".format(packetcount))

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
