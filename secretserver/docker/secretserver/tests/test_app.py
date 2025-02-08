import os
from unittest.mock import mock_open, patch


def test_root_page(client):
    """
    Sanity check
    """

    response = client.get("/")
    assert response.status_code == 200, response.data
    j = response.json
    assert j["status"] == "OK"


@patch("builtins.open", new_callable=mock_open, read_data="testdata1")
def test_get_secret_file(mock_file, client):
    """
    Get a secret from a file.
    """
    response = client.get("/secrets/secret1")
    assert response.status_code == 200, response.data
    mock_file.assert_called_with("/var/run/passwords/secret1", "r")
    j = response.json
    assert j["secret"] == "testdata1"
    assert j["error"] is None


@patch.dict(os.environ, {"SECRET_secret2": "testdata2"})
def test_get_secret_var(client):
    """
    Get a secret from an environmental variable.
    """
    response = client.get("/secrets/secret2")
    assert response.status_code == 200, response.data
    j = response.json
    assert j["secret"] == "testdata2"
    assert j["error"] is None


@patch.dict(os.environ, {}, clear=True)
def test_get_secret_notfound(client):
    """
    Try to get a secret that is neither in a file nor an environmental variable.
    """
    response = client.get("/secrets/secret3")
    assert response.status_code == 200, response.data
    j = response.json
    assert j["secret"] is None
    assert j["error"] == "secret not found"


@patch.dict(os.environ, {}, clear=True)
def test_get_secret_invalid_name(client):
    """
    Try to get a secret that has an invalid name.
    """
    response = client.get("/secrets/%20_secret")
    assert response.status_code == 200, response.data
    j = response.json
    assert j["secret"] is None
    assert j["error"] == "invalid secret name"
