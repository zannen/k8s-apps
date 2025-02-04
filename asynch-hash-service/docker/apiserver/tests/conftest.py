"""
Test fixtures and mock classes
"""

import uuid
from typing import Any, Dict

import pytest

import app


class MockJob:
    """
    A mock job, no CPU used calculating hashes
    """

    def __init__(self, job_id: str, func, **kwargs):
        self.id = job_id
        self.func = func
        self.kwargs = kwargs
        self.last_heartbeat = "recently"
        self.meta = {"nonce": "100000"}
        self.result = {
            "iter": 123,
            "nonce": ("0" * 13) + "123",
            "hash": "000000some_hash",
        }

    def get_status(self):
        return "finished"


class MockRedisQueue:
    """
    A mock Redis queue. Return jobs previously enqueued.
    """

    jobs: Dict[str, Dict[str, Any]] = {}

    def __init__(self, queue: str, conn):
        self.queue = queue
        self.conn = conn

    def enqueue(self, func, **kwargs):
        mock_job = MockJob(str(uuid.uuid4()), func, **kwargs)
        self.jobs[mock_job.id] = mock_job
        return mock_job

    def fetch_job(self, job_id: str):
        return self.jobs[job_id]


def mock_redis_queue(queue: str, conn):
    return MockRedisQueue(queue, conn)


@pytest.fixture
def flask_app():
    config = {
        "TESTING": True,
        "db_url": "sqlite+pysqlite:///:memory:",
    }
    test_flask_app = app.create_app(config)
    app.get_redis_queue = mock_redis_queue

    yield test_flask_app

    # Tidy up if needed


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()
