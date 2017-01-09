import datetime

from support.room import Room, LightsOnDuringDayRoom, GuestModeRoom, PIN_EXTERNAL_SENSOR

ROOMS = [

    GuestModeRoom(name='Living Room',
                  lights=[1, 2, 3, 27],
                  motion_pin=17,
                  motion_timeout=datetime.timedelta(minutes=15)),

    Room(name='Hallway',
         lights=[14],
         motion_pin=27,
         motion_timeout=datetime.timedelta(minutes=5)),

    LightsOnDuringDayRoom(name='Kitchen',
                          lights=[16, 17, 19],
                          motion_pin=4,
                          motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Bedroom',
         lights=[15, 20, 21, 22]),

    Room(name='Stairway',
         lights=[13],
         motion_pin=PIN_EXTERNAL_SENSOR,
         motion_timeout=datetime.timedelta(minutes=5)),
]

# Room -> Exit Neighbors. All rooms below must have motion detection. All rooms
# must have no other exits
ROOM_GRAPH = {
    'Living Room': ['Hallway'],
    'Kitchen': ['Hallway'],
}
