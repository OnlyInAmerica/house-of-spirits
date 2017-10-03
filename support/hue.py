from phue import Bridge

hue = Bridge('192.168.7.25')
hue.connect()

COMMAND_FULL_ON = {'on': True, 'bri': 254}
COMMAND_OFF = {'on': False}


def command_all_lights(command: dict):
    for light in hue.get_light_objects(mode='id'):
        hue.set_light(light, command)
