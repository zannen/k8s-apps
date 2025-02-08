"""
Provide a Flask app
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import flask


def create_app(config: Optional[Dict[str, Any]] = None):
    """
    This function is called by gunicorn and creates a Flask app.
    """
    app = flask.Flask(__name__)
    if config is None:
        config = {}
    app.config.update(config)

    log_level = os.environ.get("LOGLEVEL", "INFO")
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    app.logger.setLevel(log_level)

    @app.route("/")
    def path_root():
        return {"status": "OK"}, 200

    @app.route("/secrets/<secret_name>")
    def path_secrets_get(secret_name):
        valid_names = re.compile(r"^[a-z][A-Za-z0-9]*$")
        if not valid_names.match(secret_name):
            return {"error": "invalid secret name", "secret": None}, 200

        try:
            with open(f"/var/run/passwords/{secret_name}", "r") as fh:
                secret = fh.read()
            return {"error": None, "secret": secret}, 200
        except FileNotFoundError:
            pass

        try:
            # Try env var
            secret = os.environ[f"SECRET_{secret_name}"]
            return {"error": None, "secret": secret}, 200
        except KeyError:
            pass

        return {"error": "secret not found", "secret": None}, 200

    return app
