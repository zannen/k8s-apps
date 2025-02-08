import pytest

import app


@pytest.fixture
def flask_app():
    config = {
        "TESTING": True,
    }
    test_flask_app = app.create_app(config)

    yield test_flask_app

    # Tidy up if needed


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()
