import datetime

from support.room import Room


ROOMS = [

    Room(name='Living Room',
         lights=[1, 2, 3],
         motion_pin=17,
         motion_timeout=datetime.timedelta(minutes=20)),

    Room(name='Hallway',
         lights=[14],
         motion_pin=27,
         motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Kitchen',
         lights=[16, 17, 19],
         motion_pin=4,
         motion_timeout=datetime.timedelta(minutes=5)),

    Room(name='Bedroom',
         lights=[4, 7, 15, 18]),

    Room(name='Stairway',
         lights=[13]),
]