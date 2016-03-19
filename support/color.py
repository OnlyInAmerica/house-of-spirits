import datetime

from support.logger import get_logger
from support.time_utils import get_local_sunrise, get_local_sunset, get_local_time, get_local_dusk, get_local_dawn

LIGHT_DAYTIME_XY = [0.4506, 0.4081]
LIGHT_EVENING_XY = [0.4904, 0.4075]
LIGHT_NIGHT_XY = [0.5304, 0.4068]
LIGHT_LATENIGHT_XY = [0.6185, 0.363]

logger = get_logger("color")


def adjust_command_for_time(command: dict) -> dict:
    # Cannot set xy property if power off
    if 'on' in command and command['on'] is False:
        return command

    dawn = get_local_dawn() - datetime.timedelta(hours=1)
    sunrise = get_local_sunrise()
    sunset = get_local_sunset()
    dusk = get_local_dusk() + datetime.timedelta(hours=1)
    now = get_local_time()

    if now > dusk or now < dawn:
        command['xy'] = LIGHT_NIGHT_XY

        if now.hour < 5:  # In the wee hours, keep lights low
            command['bri'] = 124
            command['xy'] = LIGHT_LATENIGHT_XY

    elif now > sunset or now < sunrise:
        command['xy'] = LIGHT_EVENING_XY
    else:
        command['xy'] = LIGHT_DAYTIME_XY

    logger.info("Dawn %s Sunrise %s Sunset %s Dusk %s now %s. Command %s" % (
    dawn, sunrise, sunset, dusk, now, command))

    return command
