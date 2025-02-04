"""
Provide a Flask app
"""

import datetime
import hashlib
import logging
import os
import time
import urllib.parse
import uuid
from typing import Any, Dict, Optional, Tuple

import flask
import jwt
import redis
import rq
import sqlalchemy as sa

from .db import OpError, get_db

TOKEN_ISSUER = "urn:github/zannen/k8s-apps/asynch-hash-service"


def get_redis_queue(queue_name: str, conn):
    """
    Get a (possibly mocked) Redis queue.
    """
    return rq.Queue(queue_name, is_async=True, connection=conn)


def process_job(*args, **kwargs):
    """
    This is the job-processing function run by workers.
    """

    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    logger = logging.getLogger("process_job")
    logger.setLevel("INFO")
    logger.info("Processing queue job with args=%s and kwargs=%s", args, kwargs)

    job = rq.get_current_job()

    nonce = 0
    job.meta["nonce"] = nonce
    job.meta["creator"] = kwargs["creator"]
    job.save_meta()
    bdata = kwargs["data"].encode()
    hexzeros = int(kwargs["hexzeros"])
    while True:
        to_hash = bdata + f"{nonce:016d}".encode()
        h = hashlib.sha256(to_hash).hexdigest()
        if h[0:hexzeros] == "0" * hexzeros:
            del job.meta["nonce"]
            job.save_meta()
            return {
                "iter": nonce,
                "nonce": f"{nonce:016d}",
                "hash": h,
            }

        nonce += 1
        if nonce % 100000 == 0:
            logger.info("nonce=%016d", nonce)
            job.meta["nonce"] = nonce
            job.save_meta()


def setup_db(app) -> sa.engine.Engine:
    try:
        db_url_str = app.config["db_url"]
        db_pwd_str = None
    except KeyError:
        db_url_str = os.environ["DB_URL"]
        db_pwd_str = os.environ["DB_PASSWORD"]

    db_url = sa.engine.make_url(db_url_str)
    if db_pwd_str is not None:
        db_url = db_url.set(password=db_pwd_str)
    app.logger.info("Database: %s", db_url.render_as_string())

    db = None
    while db is None:
        try:
            app.logger.info("Trying to connect...")
            db = get_db(db_url)
        except OpError:
            time.sleep(1)

    app.logger.info("Connected.")
    return db


def setup_redis(app) -> Tuple[str, Any]:
    redis_url = urllib.parse.urlparse(
        os.environ.get("REDIS_URL", "redis://redis-server:6379")
    )
    app.logger.info("Redis: %s", redis_url.geturl())
    redis_queue_name = os.environ.get("REDIS_QUEUE", "q")
    redis_port = 0
    if isinstance(redis_url.port, int):
        redis_port = redis_url.port
    else:
        raise Exception("missing redis port")
    redis_conn = redis.StrictRedis(
        host=redis_url.netloc.split(":")[0],
        port=redis_port,
    )

    return redis_queue_name, redis_conn


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

    redis_queue_name, redis_conn = setup_redis(app)
    db = setup_db(app)

    token_signing_pwd = os.environ.get("TOKEN_SIGNING_PASSWORD", "secret")

    @app.route("/")
    def path_root():
        return {"status": "OK"}, 200

    @app.route("/token", methods=["POST"])
    def path_token_create():
        try:
            expires_seconds = int(flask.request.json["expires_seconds"])
            if expires_seconds < 60:
                expires_seconds = 60
            elif expires_seconds > 86400:
                expires_seconds = 86400
        except KeyError:
            expires_seconds = 3600

        issued_at = datetime.datetime.now(datetime.UTC)
        expires_at = issued_at + datetime.timedelta(seconds=expires_seconds)

        payload = {
            "iss": TOKEN_ISSUER,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "id": str(uuid.uuid4()),
        }
        token = jwt.encode(payload, token_signing_pwd, algorithm="HS256")

        return {"error": None, "token": token}, 200

    def decode_token() -> Tuple[Dict[str, str], Optional[str]]:
        err = None
        payload = {}
        try:
            token = flask.request.headers.get("API-Key", None)
            if token is None:
                raise Exception("missing token")
            payload = jwt.decode(
                token,
                token_signing_pwd,
                algorithms="HS256",
                issuer=TOKEN_ISSUER,
                options={"require": ["iss", "iat", "exp", "id"]},
            )
        except jwt.ExpiredSignatureError:
            err = "token expired"
        except jwt.InvalidIssuerError:
            err = "invalid token issuer"
        except jwt.MissingRequiredClaimError:
            err = "incomplete token"
        except Exception as exc:
            err = str(exc)

        return payload, err

    @app.route("/token/verify", methods=["POST"])
    def path_token_verify():
        _, err = decode_token()
        return {"error": err}, 200

    @app.route("/jobs", methods=["POST"])
    def path_jobs_create():
        payload, err = decode_token()
        queue = get_redis_queue(redis_queue_name, redis_conn)
        params = flask.request.get_json()
        params["creator"] = payload["id"]
        job = queue.enqueue(process_job, **params)

        return {"job": {"id": job.id}, "error": None}, 200

    @app.route("/jobs/<job_id>", methods=["GET"])
    def path_job_get(job_id):
        payload, err = decode_token()
        if err is not None:
            return {"error": err, "job": None}, 200
        queue = get_redis_queue(redis_queue_name, redis_conn)
        job = queue.fetch_job(job_id)
        if job is None:
            return {"error": "not found", "job": None}, 200

        if job.kwargs.get("creator", "") != payload["id"]:
            return {"error": "denied", "job": None}, 200
        details = {
            "id": job_id,
            "last_heartbeat": job.last_heartbeat,
            "meta": job.meta,
            "result": job.result,
            "status": job.get_status(),
        }
        return {"error": None, "job": details}, 200

    return app


class MyWorker(rq.worker.SimpleWorker):
    """
    This class is here in case worker customisations are needed.
    """
