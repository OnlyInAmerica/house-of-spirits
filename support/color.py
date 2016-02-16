from support.time_utils import get_local_sunrise, get_local_sunset, get_local_time

LIGHT_EVENING_XY = [0.5304, 0.4068]
LIGHT_DAYTIME_XY = [0.4506, 0.4081]


def add_circadian_hue_to_command(command: dict) -> dict:

    # Cannot set xy property if power off
    if 'on' in command and command['on'] is False:
        return command

    sunrise = get_local_sunrise()
    sunset = get_local_sunset()
    now = get_local_time()

    if now > sunset or now < sunrise:
        command['xy'] = LIGHT_EVENING_XY
    else:
        command['xy'] = LIGHT_DAYTIME_XY

    return command
