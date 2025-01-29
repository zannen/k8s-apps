"""
Provide a Flask app
"""

import logging
import os
import time

import flask

from .db import NotFound, OpError, create_data, get_data, get_db


def create_app(config={}):
    """
    This function is called by gunicorn and creates a Flask app.
    """
    app = flask.Flask(__name__)
    app.config.update(config)

    log_level = os.environ.get("LOGLEVEL", "INFO")
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    app.logger.setLevel(log_level)

    try:
        url = config["url"]
    except KeyError:
        db_host = os.environ.get("DB_HOST", "mysql")
        db_port = int(os.environ.get("DB_PORT", "3306"))
        db_user = os.environ.get("DB_USER", "root")
        db_pwd = os.environ.get("DB_PASSWORD", "password")
        url = f"mysql+mysqldb://{db_user}:{db_pwd}@{db_host}:{db_port}"
        url_log = f"mysql+mysqldb://{db_user}:********@{db_host}:{db_port}"
        app.logger.info("URL: %s", url_log)

    app.db = None
    while app.db is None:
        try:
            app.logger.info("Trying to connect...")
            app.db = get_db(url)
        except OpError:
            time.sleep(1)

    app.logger.info("Connected.")

    @app.route("/")
    def path_root():
        return {"status": "OK"}, 200

    # Get an existing record
    @app.route("/data/<data_id_str>", methods=["GET"])
    def path_data_get(data_id_str: int):
        data_id = None
        err = None
        info = None

        try:
            data_id = int(data_id_str)
            result = get_data(app.db, data_id)
            info = result.info
        except ValueError:
            err = "Invalid ID"
        except NotFound:
            err = "Not found"
        return {
            "error": err,
            "id": data_id,
            "info": info,
        }, 200

    # Create a record
    @app.route("/data", methods=["POST"])
    def path_data_create():
        data_id = None
        err = None
        info = None
        try:
            info = flask.request.json["info"]
            data_id = create_data(app.db, info)
        except KeyError:
            err = "No info supplied"

        return {
            "error": err,
            "id": data_id,
            "info": info,
        }, 200

    return app
