import re

from functools import wraps

import flask
from subprocess import Popen

from arrive import unlock

from SECRETS import HTTPS_API_KEY, SSL_CERT_PEM, SSL_KEY_PEM
from settings import ROOMS
from support import env
from support.logger import get_logger

app = flask.Flask(__name__)

logger = get_logger("web_server")


def is_local_request(request):
    request_remote_addr = request.environ['REMOTE_ADDR']
    return request_remote_addr.startswith('192.168.1.')


@app.route("/lights", methods=['POST'])
def lights():
    """
    example_lights_json = {
        'rooms': [
            {'name': 'Living Room', 'on': True},
        ]
    }
    """
    if is_local_request(flask.request):
        json = flask.request.get_json()
        rooms = json.get('rooms', [])
        for json_room in rooms:
            room_name = json_room['name']
            on_state = json_room['on']

            for room in ROOMS:
                if room.name == room_name:
                    room.switch(on_state)
        return "Light commands sent."
    else:
        logger.info('Guest Mode accessed by remote address %s', flask.request.environ['REMOTE_ADDR'])
        flask.abort(404)


@app.route("/guest-mode", methods=['POST'])
def guest_mode():
    if is_local_request(flask.request):
        json = flask.request.get_json()
        enabled = json.get('enabled', False)
        env.set_guest_mode(enabled)
        return "Guest mode is now %r" % enabled
    else:
        logger.info('Guest Mode accessed by remote address %s', flask.request.environ['REMOTE_ADDR'])
        flask.abort(404)


@app.route("/", methods=['GET'])
def home():
    if is_local_request(flask.request):
        home_status = {}
        for room in ROOMS:
            home_status[re.sub('[\s+]', '', room.name)] = "true" if room.is_lit() else "false"

        guest_mode = 'true' if env.is_guest_mode() else 'false'
        return flask.render_template('home.html', home_status=home_status, guest_mode=guest_mode)
    else:
        logger.info('Home accessed by remote address %s', flask.request.environ['REMOTE_ADDR'])
        flask.abort(404)


@app.route("/arrive-local", methods=['POST'])
def arrive_local():
    """
    Like arrive, but dispenses with HTTPS token checking in favor of only allowing
    local network requests
    """
    if is_local_request(flask.request):
        Popen(["python3", "./arrive.py", "run"])  # async
        return "arrive"
    else:
        logger.info('Arrive-local accessed by remote address %s', flask.request.environ['REMOTE_ADDR'])
        flask.abort(404)


@app.route("/arrive", methods=['POST'])
def arrive():
    json = flask.request.get_json()
    token = json.get('token', None)
    if token == HTTPS_API_KEY:
        Popen(["python3", "./arrive.py", "run"])  # async
        return "arrive"
    else:
        logger.warn("Request provided invalid token: %s", flask.request.values)
        flask.abort(403)


if __name__ == "__main__":
    unlock()  # Unlock any unterminated locks from last run
    context = (SSL_CERT_PEM, SSL_KEY_PEM)
    app.run(host='0.0.0.0', port=5000, ssl_context=context, threaded=True, debug=True)
