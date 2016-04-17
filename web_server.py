import flask
from subprocess import Popen

from arrive import unlock

from SECRETS import HTTPS_API_KEY, SSL_CERT_PEM, SSL_KEY_PEM
from support.logger import get_logger

app = flask.Flask(__name__)

logger = get_logger("web_server")


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
