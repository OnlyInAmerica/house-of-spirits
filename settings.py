import datetime

from support.room import Room, LightsOnDuringDayRoom, GuestModeRoom, PIN_EXTERNAL_SENSOR

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
                  lights=[16, 22, 28, 29],
                  motion_pin=6623462419764822, # Zigbee address
                  motion_timeout=datetime.timedelta(minutes=15)),

    Room(name='Kitchen',
         lights=[3, 20, 14, 15],
         motion_pin=6623462419746382, # Zigbee address
         motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Bedroom',
         lights=[1, 27]),

]

# Room -> Exit Neighbors. All rooms below must have motion detection. All rooms
# must have no other exits
ROOM_GRAPH = {
    'Living Room': ['Kitchen'],
    'Kitchen': ['Living Room'],
}

# Find in Hue app bridge settings
ZIGBEE_CHANNEL = 25