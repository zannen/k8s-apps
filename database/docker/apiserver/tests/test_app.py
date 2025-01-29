def test_root_page(flask_app):
    """
    Sanity check
    """

    with flask_app.test_client() as test_client:
        response = test_client.get("/")
        assert response.status_code == 200, response.data
        j = response.json
        assert j["status"] == "OK"


def test_data_get_nonexistent(flask_app):
    """
    Get a datum that does not exist.
    """

    with flask_app.test_client() as test_client:
        response = test_client.get("/data/1")
        assert response.status_code == 200, response.data
        j = response.json
        assert j["info"] is None
        assert j["error"] == "Not found"


def test_data_get_bad_data_id(flask_app):
    """
    Get a datum with a bad ID.
    """

    with flask_app.test_client() as test_client:
        response = test_client.get("/data/flibble")
        assert response.status_code == 200, response.data
        j = response.json
        assert j["info"] is None
        assert j["error"] == "Invalid ID"


def test_data_create_no_info(flask_app):
    """
    Create a new datum, but omit the info.
    """

    with flask_app.test_client() as test_client:
        response = test_client.post("/data", json={"no_info": "here"})
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] == "No info supplied"


def test_data_create_get(flask_app):
    """
    Create a new datum.
    """

    with flask_app.test_client() as test_client:
        response = test_client.post("/data", json={"info": "test1"})
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None
        created_id = j["id"]
        assert isinstance(created_id, int)
        assert j["info"] == "test1"

        # Get a datum that exists
        response = test_client.get(f"/data/{created_id}")
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None
        assert j["id"] == created_id
        assert j["info"] == "test1", response.data
