"""
Provide a Flask app
"""

import datetime
import hashlib
import logging
import os
import urllib.parse
import uuid
from typing import Any, Dict, Optional, Tuple

import flask
import jwt
import redis
import rq

TOKEN_ISSUER = "urn:github/zannen/k8s-apps/async-hash-service"


def get_redis_queue(queue_name: str, conn):
    """
    Get a (possibly mocked) Redis queue.
    """
    return rq.Queue(queue_name, is_async=True, connection=conn)


def process_job(*args, **kwargs):
    """
    This is the job-processing function run by workers.
    """
    job = rq.get_current_job()

    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    logger = logging.getLogger("process_job")
    logger.setLevel("INFO")
    logger.info(
        "%s: Processing queue job with args=%s and kwargs=%s",
        job.id,
        args,
        kwargs,
    )

    nonce = 0
    job.meta["nonce"] = nonce
    job.meta["creator"] = kwargs["creator"]
    job.save_meta()
    bdata = kwargs["data"].encode()
    hexzeros = int(kwargs["hexzeros"])
    update_every = kwargs.get("update_every", 100000)
    while True:
        to_hash = bdata + f"{nonce:016d}".encode()
        h = hashlib.sha256(to_hash).hexdigest()
        if h[0:hexzeros] == "0" * hexzeros:
            break

        nonce += 1
        if nonce % update_every == 0:
            logger.info("%s: nonce=%016d ...", job.id, nonce)
            job.meta["nonce"] = nonce
            job.save_meta()

    del job.meta["nonce"]
    job.save_meta()
    logger.info("%s: nonce=%016d, job ends", job.id, nonce)
    return {"final_hash": h, "nonce": nonce}


def setup_redis(app: flask.Flask) -> rq.Queue:
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
    return get_redis_queue(redis_queue_name, redis_conn)


def create_app(config: Optional[Dict[str, Any]] = None) -> flask.Flask:
    """
    This function is called by gunicorn and creates a Flask app.
    """
    app = flask.Flask(__name__)
    if config is None:
        config = {"TESTING": False}
    app.config.update(config)

    log_level = os.environ.get("LOGLEVEL", "INFO")
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    app.logger.setLevel(log_level)

    redis_queue = setup_redis(app)

    token_signing_pwd = os.environ.get("TOKEN_SIGNING_PASSWORD", "secret")

    @app.route("/")
    def path_root() -> Tuple[Dict[str, str], int]:
        return {"status": "OK"}, 200

    @app.route("/token", methods=["POST"])
    def path_token_create() -> Tuple[Dict[str, Any], int]:
        expires_seconds = 3600
        if isinstance(flask.request.json, dict):
            expires_seconds = int(
                flask.request.json.get("expires_seconds", 3600)
            )
            if expires_seconds < 60:
                expires_seconds = 60
            elif expires_seconds > 86400:
                expires_seconds = 86400

        issued_at = datetime.datetime.now(datetime.UTC)
        expires_at = issued_at + datetime.timedelta(seconds=expires_seconds)

        payload: Dict[str, Any] = {
            "iss": TOKEN_ISSUER,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "id": str(uuid.uuid4()),
        }
        token = jwt.encode(payload, token_signing_pwd, algorithm="HS256")

        return {"error": None, "token": token}, 200

    def decode_token() -> Tuple[Dict[str, str], Optional[str]]:
        err = None
        payload: Dict[str, Any] = {}
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
    def path_token_verify() -> Tuple[Dict[str, Any], int]:
        _, err = decode_token()
        return {"error": err}, 200

    @app.route("/jobs", methods=["POST"])
    def path_jobs_create() -> Tuple[Dict[str, Any], int]:
        payload, err = decode_token()
        params = flask.request.get_json()
        params["creator"] = payload["id"]
        job = redis_queue.enqueue(process_job, **params)
        if app.config["TESTING"]:
            # jobs are run synchronously in testing
            assert job.is_finished

        return {"error": None, "job": {"id": job.id}}, 200

    @app.route("/jobs/<job_id>", methods=["GET"])
    def path_job_get(job_id: str) -> Tuple[Dict[str, Any], int]:
        payload, err = decode_token()
        if err is not None:
            return {"error": err, "job": None}, 200

        # Check redis
        job = redis_queue.fetch_job(job_id)
        if job is None:
            return {"error": "not found", "job": None}, 200

        # check ownership
        if job.meta.get("creator", "") != payload["id"]:
            app.logger.warning(
                "Job ownership mismatch (Redis): %s owned by %s, req by %s",
                job_id,
                job.meta.get("creator", ""),
                payload["id"],
            )
            # returning "access denied" would leak info
            return {"error": "not found", "job": None}, 200

        status = job.get_status()
        result = job.return_value()
        details: Dict[str, Any] = {
            "extra": {},
            "final_hash": None,
            "id": job_id,
            "nonce": None,
            "owner_id": job.meta.get("creator", ""),
            "status": status,
        }
        if status == "finished" and isinstance(result, dict):
            details["final_hash"] = result.get("final_hash", "")
            details["nonce"] = result.get("nonce", 0)
        else:
            details["extra"] = {
                "last_heartbeat": job.last_heartbeat,
                "nonce": job.meta.get("nonce", 0),
            }

        return {"error": None, "job": details}, 200

    return app


class MyWorker(rq.worker.SimpleWorker):
    """
    This class is here in case worker customisations are needed.
    """
