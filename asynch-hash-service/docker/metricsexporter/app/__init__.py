"""
Provide a Flask app
"""

import datetime
import logging
import os
import urllib.parse
from typing import Any, Dict, List, Optional

import flask
import redis
import rq

# for `API` and `API_VER`, see the APIService definition.
API = "custom.metrics.k8s.io"
API_VER = "v1beta1"


def queue_job_count(queue, job_statuses: List[str]) -> int:
    """
    This function counts jobs that in the given state(s) for a given queue.
    """
    jobs = [
        job_id
        for job_id in queue.job_ids
        if queue.fetch_job(job_id).get_status(refresh=True) in job_statuses
    ]
    return len(jobs)


def queue_busy_workers(queue: str) -> List[str]:
    """
    This function counts the number of busy workers for a given queue.
    """
    return [
        worker.name
        for worker in rq.Worker.all(queue=queue)
        if worker.state == "busy"
    ]


def create_metrics_exporter_app(config: Optional[Dict[str, Any]] = None):
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

    app.redis_url = urllib.parse.urlparse(
        os.environ.get(
            "REDIS_URL",
            "redis://redis-server.ns.svc.cluster.local:6379",
        ),
    )

    app.redis_connections: Dict[str, redis.StrictRedis] = {}

    def get_redis_connection(namespace: str) -> redis.StrictRedis:
        host = app.redis_url.netloc.split(".")
        host[1] = namespace
        namespaced_url = app.redis_url._replace(netloc=".".join(host))
        key = namespaced_url.geturl()
        try:
            conn = app.redis_connections[key]
        except KeyError:
            conn = redis.StrictRedis(
                host=namespaced_url.netloc.split(":")[0],
                port=namespaced_url.port,
            )
            app.redis_connections[key] = conn

        return conn

    app.get_redis_connection = get_redis_connection

    app.logger.info("Redis: %s", app.redis_url.geturl())

    base_path = f"/apis/{API}/{API_VER}"
    metric_path = (
        f"{base_path}/namespaces/<namespace>/deployments.apps/<deployment_app>"
        "/<metric>"
    )

    def redisqueue_length(namespace, deployment_app, metric):
        """
        Return a metric that indicates how many redis queue workers there
        should be. This needs to include 2 components:
        - the number of queued jobs: more queued jobs, more workers needed
        - the number of busy workers: don't scale down and kill busy workers
        """
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        content = {
            "kind": "MetricValueList",
            "apiVersion": f"{API}/{API_VER}",
            "metadata": {"selflink": f"{base_path}/"},
            "items": [
                {
                    "describedObject": {
                        "kind": "Deployment",
                        "namespace": namespace,
                        "name": deployment_app,
                        "apiVersion": "apps/v1",
                    },
                    "metricName": "count",
                    "timestamp": now,
                    "value": "0",
                },
            ],
        }

        try:
            # For `metricLabelSelector`, see `matchLabels` in rq-worker-*.yaml.
            mls = flask.request.args.get("metricLabelSelector")

            if not mls.startswith("queues="):
                return content, 200

            # Contact the redis server in the given namespace. This is because
            # Kubernetes objectes of kind APIService are not namespaced, so the
            # custom metrics server in one namespace needs to be able to query
            # the redis server in any other namespace.
            redis_conn = app.get_redis_connection(namespace)
            all_busy_workers: List[str] = []
            qinfo = {}
            value = 0
            for qname in mls[7:].split("-"):
                queue = rq.Queue(qname, connection=redis_conn)
                job_count = queue_job_count(queue, ["queued"])
                busy_workers = queue_busy_workers(queue)
                qinfo[qname] = {
                    "queued_job_count": job_count,
                    "busy_workers": busy_workers,
                }
                value += job_count
                all_busy_workers += busy_workers

            # Since rq workers may service more than one queue, avoid counting
            # workers more than once.
            all_busy_workers = list(set(all_busy_workers))
            value += len(all_busy_workers)

            content["items"][0]["_debug"] = {
                "all_busy_workers": all_busy_workers,
                "queue_info": qinfo,
            }
            content["items"][0]["value"] = str(value)

        except Exception as exc:
            app.logger.warning("Swallowed an Exception: %s", str(exc))
            content["error"] = str(exc)

        # Always return HTTP 200, even after catching an exception, so that the
        # error can be easily seen with:
        # kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/..."
        return content, 200

    metrics = {
        "redisqueue_length": redisqueue_length,
    }

    @app.route(f"{base_path}")
    @app.route(f"{base_path}/")
    def path_root():
        return {
            "kind": "APIResourceList",
            "apiVersion": "v1",
            "groupVersion": f"{API}/{API_VER}",
            "resources": [
                {
                    "name": f"deployments.apps/{metric_name}",
                    "singularName": "",
                    "namespaced": True,
                    "kind": "MetricValueList",
                    "verbs": ["get"],
                }
                for metric_name in sorted(metrics.keys())
            ],
        }, 200

    @app.route(metric_path)
    def path_deploymentsapps_metric(namespace, deployment_app, metric):
        func = metrics.get(metric, None)
        if func is None:
            content = {
                "apiVersion": f"{API}/{API_VER}",
                "error": "metric not found",
                "items": [],
                "kind": "MetricValueList",
                "metadata": {"selflink": f"{base_path}/"},
            }
            return content, 200

        return func(namespace, deployment_app, metric)

    return app
