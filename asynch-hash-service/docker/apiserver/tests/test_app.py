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

    # Get a token
    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token = j["token"]

    # Verify the token
    response = client.post(
        "/token/verify",
        headers={"API-Key": token},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None, response.data


def test_job_nonexistant(client):
    """
    Test job creation and fetching
    """

    # Get a token
    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token = j["token"]

    # Get a nonexistent job with the correct token
    response = client.get(
        "/jobs/00000000-0000-0000-0000-000000000000",
        headers={"API-Key": token},
        json={},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] == "not found"


def test_job_create_get(client):
    """
    Test job creation and fetching
    """

    # Get a token
    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token = j["token"]

    # Create a job
    response = client.post(
        "/jobs",
        headers={"API-Key": token},
        json={
            "data": "test",
            "hexzeros": 2,
            "update_every": 100,
        },
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    job_id = j["job"]["id"]

    # Get the job with no token
    response = client.get(
        f"/jobs/{job_id}",
        headers={},  # no token
        json={},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] == "missing token"

    # Get the job with the correct token
    response = client.get(
        f"/jobs/{job_id}",
        headers={"API-Key": token},
        json={},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None, response.data
    assert isinstance(j["job"], dict)
    assert j["job"]["status"] == "finished"
    assert j["job"]["nonce"] == 227, response.data

    # Get a second token
    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token2 = j["token"]

    # Get the job with the incorrect token
    response = client.get(
        f"/jobs/{job_id}",
        headers={"API-Key": token2},
        json={},
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] == "not found"
