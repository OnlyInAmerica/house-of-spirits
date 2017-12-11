import json
from subprocess import Popen

import copy
import flask
import re

from gevent import pywsgi
from settings import ROOMS
from support import env
from support.color import get_current_circadian_color
from support.hue import command_all_lights, COMMAND_FULL_ON
from support.logger import get_logger
from support.time_utils import get_local_time

app = flask.Flask(__name__)

logger = get_logger("web_server")

party_process = None  # Party mode process


def get_home_status(template_friendly_dict: bool) -> dict:
    """
    :param template_friendly_dict: whether to create a template friendly dict. This involves representing booleans
    as "true"/"false" strings and stripping spaces from keys. For template dicts,
    we need to use string values, for json return we can use bool
    """

    home_status = {}
    for room in ROOMS:
        lit = room.is_lit()
        occupied = env.get_room_occupied(room.name)
        key = room.name
        if template_friendly_dict:
            lit = "true" if lit else "false"
            occupied = "true" if occupied else "false"
            key = re.sub('[\s+]', '', key)

        home_status[key] = {'lit': lit, 'occupied': occupied}
    logger.info(home_status)
    return home_status


@app.route("/party-mode", methods=['POST'])
def party():
    global party_process
    json = flask.request.get_json()
    enabled = json.get('enabled', False)
    logger.info('Got party state %r' % enabled)
    if enabled and not env.is_party_mode():
        # Start party XD
        party_process = Popen(["python3", "./animate_web.py", "run"])  # async
        env.set_party_mode(True)
        env.set_motion_enabled(False)

    elif not enabled and env.is_party_mode():
        # Stop party :(
        env.set_party_mode(False)
        env.set_motion_enabled(True)
        if party_process is not None:
            party_process.kill()
            party_process = None

        # Return lights to circadian color
        command = copy.deepcopy(COMMAND_FULL_ON)
        circadian_color = get_current_circadian_color(date=get_local_time())
        command_all_lights(circadian_color.apply_to_command(command))
    return "Party mode is now %r" % enabled


@app.route("/lights", methods=['POST'])
def lights():
    """
    example_lights_json = {
        'rooms': [
            {'name': 'Living Room', 'on': True},
        ]
    }
    """
    json = flask.request.get_json()
    rooms = json.get('rooms', [])
    logger.info('Switching rooms %s', rooms)
    for json_room in rooms:
        room_name = json_room['name']
        on_state = json_room['on']

        for room in ROOMS:
            # Strip whitespace
            if room.name == room_name:
                logger.info('Switching room %s', room.name)
                room.switch(on_state)
    return "Light commands sent."


@app.route("/guest-mode", methods=['POST'])
def guest_mode():
    json = flask.request.get_json()
    enabled = json.get('enabled', False)
    env.set_guest_mode(enabled)
    return "Guest mode is now %r" % enabled


@app.route("/motion-mode", methods=['POST'])
def motion_mode():
    json = flask.request.get_json()
    enabled = json.get('enabled', False)
    env.set_motion_enabled(enabled)
    return "Motion mode is now %r" % enabled


@app.route("/vacation-mode", methods=['POST'])
def vacation_mode():
    json = flask.request.get_json()
    enabled = json.get('enabled', False)
    env.set_vacation_mode(enabled)
    return "Vacation mode is now %r" % enabled


@app.route("/home-state", methods=['GET'])
def home_status():
    home_status = get_home_status(template_friendly_dict=False)  # bools safe for json
    return json.dumps(home_status)


@app.route("/", methods=['GET'])
def home():
    home_status_json = get_home_status(template_friendly_dict=False)  # Template engine requires string values
    guest_mode = 'true' if env.is_guest_mode() else 'false'
    party_mode = 'true' if env.is_party_mode() else 'false'
    motion_mode = 'true' if env.is_motion_enabled() else 'false'
    vacation_mode = 'true' if env.is_vacation_mode() else 'false'

    return flask.render_template('home.html',
                                 home_status=home_status_json,
                                 guest_mode=guest_mode,
                                 party_mode=party_mode,
                                 motion_mode=motion_mode,
                                 vacation_mode=vacation_mode)


if __name__ == "__main__":

    env.set_party_mode(False)

    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
