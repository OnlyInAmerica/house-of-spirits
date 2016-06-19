import time

# Savannah's 'Tropical sunset' palette
import copy

from support.hue import hue
from support.logger import get_logger

FRAME_TIME_S = 10

COLORS = [
    [0.1772, 0.0592],  # Blue
    [0.4882, 0.2286],  # Pink
    [0.6043, 0.3728],  # Sun Amber
    [0.6736, 0.3221],  # Red
    [0.6043, 0.3728],  # Sun Amber
    [0.4882, 0.2286],  # Pink
]

PROCESS_NAME = 'animate'

logger = get_logger("animate")

command = {'on': True,
           'bri': 254,
           'transitiontime': 10 * FRAME_TIME_S}

LIGHT_TO_COLOR_IDX = {}
counter = 0


def assign_colors(offset: int = 0):
    colors_idx = offset
    for light in hue.get_light_objects(mode='id'):

        LIGHT_TO_COLOR_IDX[light] = colors_idx
        #logger.info("Light %d will have color %d :  %s" % (light, colors_idx, COLORS[colors_idx]))

        if colors_idx == len(COLORS) - 1:
            colors_idx = 0
        else:
            colors_idx += 1


while True:

    assign_colors(offset=counter)

    if counter == len(COLORS) - 1:
        counter = 0
    else:
        counter += 1

    for light, colors_idx in LIGHT_TO_COLOR_IDX.items():
        command_copy = copy.deepcopy(command)
        command_copy['xy'] = COLORS[colors_idx]
        #logger.info("Animating light to %s" % command_copy)
        hue.set_light(light, command_copy)
    #logger.info("Sleeping %d s" % FRAME_TIME_S)
    time.sleep(FRAME_TIME_S + 1)
