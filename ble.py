import time

import struct
from bluepy.bluepy.btle import Peripheral, DefaultDelegate, BTLEException

from settings import ROOMS
from support.env import set_room_last_motion_date
from support.logger import get_logger
from support.time_utils import get_local_time

"""
BLE Wireless sensor control
To configure and enable BLE::

    sudo hciconfig hci0 down
    sudo btmgmt le on
    sudo btmgmt bredr off
    sudo hciconfig hci0 up
"""
logger = get_logger("ble")

TARGET_ROOM = ROOMS[4]
SENSOR_BTLE_MAC = "D4:02:D4:BF:E5:2B"


class BleDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(cHandle, data):
        logger.info("Got motion notification! Switching room %s", TARGET_ROOM.name)
        TARGET_ROOM.switch(True, adjust_hue_for_time=False)
        set_room_last_motion_date(TARGET_ROOM.name, get_local_time())

while True:
    try:
        logger.info("Connecting to motion sensor...")
        peripheral = Peripheral(SENSOR_BTLE_MAC, "random")
        logger.info("Connected to motion sensor!")
        peripheral.withDelegate(BleDelegate)

        peripheral.writeCharacteristic(14, struct.pack('<bb', 0x01, 0x00), withResponse=True)

        logger.info("Awaiting notification")
        while True:
            result = peripheral.waitForNotifications(0)

    except BTLEException:
        logger.exception("BLE Error")
        time.sleep(5)
