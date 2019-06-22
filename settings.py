import datetime

from support.room import Room, LightsOnDuringDayRoom, GuestModeRoom, PIN_EXTERNAL_SENSOR
from support.zigbee_addrs import SENSOR_NAME_TO_ADDR

# 225 Montecito Light index -> description
# 1 - Sav's bed
# 3 - Hall dome North
# 14 - Kitchen dome South
# 15 - Kitchen dome North
# 16 - Desk
# 20 - Hall dome South
# 22 - Torch
# 27 - David bed

ROOMS = [

    GuestModeRoom(name='Living Room',
                  lights=[16, 22, 28, 29, 32],
                  motion_pin=SENSOR_NAME_TO_ADDR['Living Room Sensor'], # Zigbee address
                  motion_timeout=datetime.timedelta(minutes=15)),

    # A pseud-room, used to cover exit from Living Room
    Room(name='Kitchen Hall',
         lights=[],
         motion_pin=SENSOR_NAME_TO_ADDR['Kitchen Hall Sensor'], # Zigbee address
         motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Kitchen',
         lights=[3, 20, 14, 15],
         motion_pin=SENSOR_NAME_TO_ADDR['Kitchen Sensor'], # Zigbee address
         motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Bedroom',
         lights=[1, 27]),

]

# Room -> Exit Neighbors. All rooms below must have motion detection. All key rooms
# must have no other exits
ROOM_GRAPH = {
    'Living Room': ['Kitchen Hall'],
}

ZIGBEE_UDP_PORT = 5005
