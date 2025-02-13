"""
Provide a Flask app
"""

import collections
import logging
import os
import time
from typing import Any, Dict

import flask
import redis
import rq
import rq.worker
import yaml


def queue_func(*args, **kwargs):
    """
    This is the job-processing function run by workers.

    For test purposes, it simply sleeps for the specified time.
    """
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    logger = logging.getLogger("queue_func")
    logger.setLevel("INFO")
    logger.info("Processing queue job with args=%s and kwargs=%s", args, kwargs)
    if "sleep" in kwargs:
        time.sleep(int(kwargs["sleep"]))
    return {
        "queue_func_result": {
            "args": args,
            "kwargs": kwargs,
        },
    }


def worker_info(worker) -> dict:
    content: Dict[str, Any] = {
        "queues": [queue.name for queue in worker.queues],
    }
    for attr in [
        "birth_date",
        # "current_job",
        "failed_job_count",
        "hostname",
        "last_heartbeat",
        "name",
        "pid",
        # "queues",
        "state",
        "successful_job_count",
        "total_working_time",
    ]:
        try:
            content[attr] = getattr(worker, attr)
        except AttributeError:
            content[attr] = "<<attr not found>>"
    return content


def create_apiserver_app(config={}):
    """
    This function is called by gunicorn and creates a Flask app.
    """
    app = flask.Flask(__name__)
    app.config.update(config)

    app.redis_host = os.environ.get("REDIS_HOST", "redis-server")
    app.redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    app.redis_conn = redis.StrictRedis(
        host=app.redis_host,
        port=app.redis_port,
    )

    log_level = os.environ.get("LOGLEVEL", "INFO")
    logging.basicConfig(format="[%(asctime)-15s] [%(levelname)s] %(message)s")
    app.logger.setLevel(log_level)
    app.logger.info("Redis: %s:%s", app.redis_host, app.redis_port)

    @app.route("/")
    def path_root():
        return {"status": "OK"}, 200

    @app.route("/queues/<queue_name>/jobs")
    def path_queue_jobs(queue_name):
        queue = rq.Queue(queue_name, connection=app.redis_conn)
        jobs = {}
        for job_id in queue.job_ids:
            job = queue.fetch_job(job_id)
            if job is None:
                jobs[job_id] = {"error": "job not found"}
            else:
                jobs[job_id] = {
                    "id": job.id,
                    "result": job.result,
                    "status": job.get_status(),
                }
        return {"jobs": jobs}, 200

    @app.route("/queues/<queue_name>/length")
    def path_queue_length(queue_name):
        queue = rq.Queue(queue_name, connection=app.redis_conn)
        return {"length": len(queue)}, 200

    @app.route("/queues/<queue_name>/counts")
    def path_queue_counts(queue_name):
        queue = rq.Queue(queue_name, connection=app.redis_conn)
        counts = collections.defaultdict(lambda: 0)
        for job_id in queue.job_ids:
            job = queue.fetch_job(job_id)
            if job is None:
                continue
            status = job.get_status(refresh=True)
            counts[status] += 1
        return {"counts": counts}, 200

    @app.route("/queues/<queue_name>/enqueue", methods=["POST"])
    def path_queue_enqueue(queue_name):
        sync = flask.request.args.get("sync", "false").lower()
        is_async = not yaml.safe_load(sync)
        queue = rq.Queue(
            queue_name,
            is_async=is_async,
            connection=app.redis_conn,
        )
        job = queue.enqueue(
            queue_func,
            **flask.request.get_json(),
        )
        return {
            "job": {
                "id": job.id,
                "result": job.result,  # None for async job
                "status": job.get_status(),
            },
        }, 200

    @app.route("/queues/<queue_name>/jobs/<job_id>")
    def path_queue_job(queue_name, job_id):
        queue = rq.Queue(queue_name, connection=app.redis_conn)
        job = queue.fetch_job(job_id)
        if job is None:
            return {"error": "job not found"}, 404
        return {
            "job": {
                "id": job.id,
                "result": job.result,
                "status": job.get_status(),
            },
        }, 200

    @app.route("/queues/<queue_name>/workers")
    def path_queue_workers(queue_name):
        queue = rq.Queue(queue_name, connection=app.redis_conn)
        redis_workers = rq.Worker.all(queue=queue)
        workers = [worker_info(worker) for worker in redis_workers]
        return {"workers": workers}, 200

    @app.route("/workers")
    def path_workers():
        redis_workers = rq.Worker.all(connection=app.redis_conn)
        workers = [worker_info(worker) for worker in redis_workers]
        return {"workers": workers}, 200

    return app


class MyWorker(rq.worker.SimpleWorker):
    """
    This class is here in case worker customisations are needed.
    """
