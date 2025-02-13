from typing import List

import app


def test_root_page(client):
    """
    Sanity check
    """

    base_path = f"/apis/{app.API}/{app.API_VER}"
    response = client.get(base_path)
    assert response.status_code == 200, response.data
    j = response.json
    assert j["groupVersion"] == f"{app.API}/{app.API_VER}"


def test_redisqueue_length_without_metricLabelSelector(client):
    """
    Test getting a redis queue length
    """

    base_path = f"/apis/{app.API}/{app.API_VER}"
    metric_path = (
        f"{base_path}/namespaces/SOME_NS/deployments.apps/DEPLOYMENT"
        "/redisqueue_length"
    )

    response = client.get(metric_path)
    assert response.status_code == 200, response.data
    j = response.json
    assert "error" in j
    assert j["error"] == "missing/invalid metricLabelSelector"
    assert j["kind"] == "MetricValueList"


class MockStrictRedis:
    """
    A mock StrictRedis instance.
    """

    def __init__(self, host="unknownhost", port=1234):
        self.host = host
        self.port = port


class MockJob:
    """
    A mock rq.job.Job.
    """

    def __init__(self, job_id: str):
        self.id = job_id

    def get_status(self, refresh=False):
        return "queued"


class MockrqQueue:
    """
    A mock rq.Queue.
    """

    job_ids = ["job1", "job2", "job3"]

    def __init__(
        self,
        queue_name: str,
        is_async: bool,
        connection: MockStrictRedis,
    ):
        self.queue_name = queue_name
        self.is_async = is_async
        self.connection = connection

    def fetch_job(self, job_id: str) -> MockJob:
        return MockJob(job_id)


class MockrqWorker:
    """
    A mock rq.Worker.
    """

    state = "busy"

    def __init__(self, name: str):
        self.name = name

    @classmethod
    def all(cls, queue: str) -> List["MockrqWorker"]:
        return [MockrqWorker("abc"), MockrqWorker("def"), MockrqWorker("ghi")]


def test_redisqueue_length(client):
    """
    Test getting a redis queue length
    """

    base_path = f"/apis/{app.API}/{app.API_VER}"
    metric_path = (
        f"{base_path}/namespaces/SOME_NS/deployments.apps/DEPLOYMENT"
        "/redisqueue_length"
    )

    app.redis.StrictRedis = MockStrictRedis
    app.rq.Queue = MockrqQueue
    app.rq.Worker = MockrqWorker
    query = {
        "metricLabelSelector": "queues=queue1-queue2",
    }
    response = client.get(metric_path, query_string=query)
    assert response.status_code == 200, response.data
    j = response.json
    assert "error" not in j, j["error"] + j["error_trace"]
    assert j["kind"] == "MetricValueList"
    assert isinstance(j["items"], list)
    assert len(j["items"]) == 1

    # 3 jobs in 2 queues, plus 3 busy workers, so a value of 9 total.
    assert j["items"][0]["value"] == "9"
