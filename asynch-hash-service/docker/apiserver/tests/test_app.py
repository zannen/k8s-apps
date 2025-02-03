def test_root_page(client):
    """
    Sanity check
    """

    response = client.get("/")
    assert response.status_code == 200, response.data
    j = response.json
    assert j["status"] == "OK"


def test_token(flask_app):
    """
    Test token issuing and verifying
    """

    with flask_app.test_client() as test_client:
        response = test_client.post("/token", json={})
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None
        token = j["token"]

        response = test_client.post(
            "/token/verify",
            headers={"API-Key": token},
        )
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None, response.data


def test_job_create_get(flask_app):
    with flask_app.test_client() as test_client:
        response = test_client.post("/token", json={})
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None
        token = j["token"]

        response = test_client.post(
            "/jobs",
            headers={"API-Key": token},
            json={},
        )
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None
        job_id = j["job"]["id"]

        response = test_client.get(
            f"/jobs/{job_id}",
            headers={"API-Key": token},
            json={},
        )
        assert response.status_code == 200, response.data
        j = response.json
        assert j["error"] is None
