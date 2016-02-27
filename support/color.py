from support.logger import get_logger
from support.time_utils import get_local_sunrise, get_local_sunset, get_local_time, get_local_dusk, get_local_dawn

LIGHT_DUSK_XY = [0.5304, 0.4068]
LIGHT_SUNSET_XY = [0.4904, 0.4075]
LIGHT_DAYTIME_XY = [0.4506, 0.4081]

logger = get_logger("color")


def add_circadian_hue_to_command(command: dict) -> dict:
    # Cannot set xy property if power off
    if 'on' in command and command['on'] is False:
        return command

    dawn = get_local_dawn()
    sunrise = get_local_sunrise()
    sunset = get_local_sunset()
    dusk = get_local_dusk()
    now = get_local_time()

    if now > dusk or now < dawn:
        command['xy'] = LIGHT_DUSK_XY
    elif now > sunset or now < sunrise:
        command['xy'] = LIGHT_SUNSET_XY
    else:
        command['xy'] = LIGHT_DAYTIME_XY

    logger.info("Dawn %s Sunrise %s Sunset %s Dusk %s now %s. Color %s" % (
    dawn, sunrise, sunset, dusk, now, command['xy']))

    return command
