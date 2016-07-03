import datetime

from support.room import Room, LightsOnDuringDayRoom, GuestModeRoom, PIN_EXTERNAL_SENSOR

ROOMS = [

    GuestModeRoom(name='Living Room',
                  lights=[1, 2, 3],
                  motion_pin=17,
                  motion_timeout=datetime.timedelta(minutes=20)),

    Room(name='Hallway',
         lights=[14],
         motion_pin=27,
         motion_timeout=datetime.timedelta(minutes=5)),

    LightsOnDuringDayRoom(name='Kitchen',
                          lights=[16, 17, 19],
                          motion_pin=4,
                          motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Bedroom',
         lights=[4, 7, 15, 18]),

    Room(name='Stairway',
         lights=[13],
         motion_pin=PIN_EXTERNAL_SENSOR,
         motion_timeout=datetime.timedelta(minutes=5)),
]

ROOM_GRAPH = {
    'Living Room': ['Hallway'],
    'Kitchen': ['Hallway']
}
