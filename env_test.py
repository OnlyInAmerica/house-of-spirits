import time

import datetime

from support.env import set_party_mode, is_party_mode, set_room_occupied, get_room_occupied, set_room_last_motion_date, get_room_last_motion_date

while True:
    time.sleep(1)

    # party = is_party_mode()
    # print("Is party mode %r" % party)
    # set_party_mode(not party)

    # occupied = get_room_occupied("fake_room")
    # print("Room occupied %r" % occupied)
    # set_room_occupied("fake_room", not occupied)

    last_motion_date = get_room_last_motion_date("fake_room")
    print("Room last_motion_date %s" % last_motion_date)
    set_room_last_motion_date("fake_room", datetime.datetime.now())
