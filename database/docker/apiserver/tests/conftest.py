import pytest

import app


@pytest.fixture
def flask_app():
    url = "sqlite+pysqlite:///:memory:"
    return app.create_app({"url": url})
