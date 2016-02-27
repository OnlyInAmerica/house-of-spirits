from flask import Flask

from support.circadian_utils import adjust_light_for_event
from support.hue import hue
from support.time_utils import SUNSET, SUNRISE

app = Flask(__name__)


@app.route("/evening")
def sunset():
    for light in hue.get_light_objects(mode='id'):
        adjust_light_for_event(light, SUNSET)
    return "evening"


@app.route("/daylight")
def sunrise():
    for light in hue.get_light_objects(mode='id'):
        adjust_light_for_event(light, SUNRISE)
    return "daylight"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
