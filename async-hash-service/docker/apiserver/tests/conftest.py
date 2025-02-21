"""
Test fixtures and mock classes
"""

import fakeredis
import pytest
import rq

import app


def mock_redis_queue(queue_name: str, conn) -> rq.Queue:
    """
    Get a mocked Redis queue.
    """

    # Ignore the provided connection, use a fake one
    conn = fakeredis.FakeStrictRedis()
    return rq.Queue(queue_name, is_async=False, connection=conn)


@pytest.fixture
def flask_app():
    config = {"TESTING": True}
    app.get_redis_queue = mock_redis_queue
    test_flask_app = app.create_app(config)

    yield test_flask_app

    # Tidy up if needed


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()
