import copy
from flask import Flask

from support.color import LIGHT_EVENING_XY, LIGHT_DAYTIME_XY
from support.hue import hue, command_all_lights
from support.time_utils import SUNSET, SUNRISE

app = Flask(__name__)


@app.route("/evening")
def sunset():
    command = copy.deepcopy(LIGHT_EVENING_XY)  # Don't alter reference command
    command_all_lights(command)
    return "evening"


@app.route("/daylight")
def sunrise():
    command = copy.deepcopy(LIGHT_DAYTIME_XY)  # Don't alter reference command
    command_all_lights(command)
    return "daylight"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
