"""
Provide a Flask app
"""

import logging
import os
import re

import flask


def create_app(config={}):
    """
    This function is called by gunicorn and creates a Flask app.
    """
    app = flask.Flask(__name__)
    app.config.update(config)

    log_level = os.environ.get("LOGLEVEL", "INFO")
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    app.logger.setLevel(log_level)

    @app.route("/")
    def path_root():
        return {"status": "OK"}, 200

    @app.route("/secrets/<secret_name>")
    def path_secrets_get(secret_name):
        err = None
        secret = ""

        valid_names = re.compile(r"^[a-z][A-Za-z0-9]*$")
        if valid_names.match(secret_name):
            try:
                with open(f"/var/run/passwords/{secret_name}", "r") as fh:
                    secret = fh.read()
            except FileNotFoundError:
                err = "secret not found"
        else:
            err = "invalid secret name"
        return {
            "error": err,
            "secret": secret,
        }, 200

    return app
