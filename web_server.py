import json

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
        home_status = []
        for room in ROOMS:
            home_status.append({'name': room.name,
                                'status': "On" if room.is_lit() else "Off"})

        guest_mode = env.is_guest_mode()
        return flask.render_template('home.html', home_status=home_status, guest_mode=guest_mode)
    else:
        logger.info('Home accessed by remote address %s', flask.request.environ['REMOTE_ADDR'])
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
