def test_root_page(client):
    """
    Sanity check
    """

    response = client.get("/")
    assert response.status_code == 200, response.data
    j = response.json
    assert j["status"] == "OK"


def test_token(client):
    """
    Test token issuing and verifying
    """

    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token = j["token"]

    response = client.post(
        "/token/verify",
        headers={"API-Key": token},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None, response.data


def test_job_create_get(client):
    """
    Test job creation and fetching
    """

    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token = j["token"]

    response = client.post(
        "/jobs",
        headers={"API-Key": token},
        json={},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    job_id = j["job"]["id"]

    response = client.get(
        f"/jobs/{job_id}",
        headers={"API-Key": token},
        json={},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
