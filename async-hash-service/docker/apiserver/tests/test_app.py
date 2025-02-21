import pytest


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


@pytest.mark.parametrize(
    "testdata, zeros, expected_nonce, expected_hash",
    [
        (
            "test",
            0,
            0,
            "cab2614f067dc57faa95a99d2295fac791d16c28996ce54d4cbbca0b5f08330b",
        ),
        (
            "test",
            1,
            30,
            "0e46f170af1e06d7b6346314c0fe5d21a1955b7f091886bc9d1af8ffacd4fb4f",
        ),
        (
            "test",
            2,
            227,
            "0083bcbb41080af40a9c581845dd6c5c72bf937272d8bc9df20662b4fb95a703",
        ),
        (
            "test",
            3,
            1472,
            "00048394de3d4cf79895499a60e93210c0caf35d78a258e0f3c9f4033b4accb4",
        ),
        (
            "test",
            4,
            33536,
            "000033b7940d43751faba7c5e08036e58836d1dbbdbad052cde8a3f60e572edf",
        ),
    ],
)
def test_job_results(
    client,
    testdata: str,
    zeros: int,
    expected_nonce: int,
    expected_hash: str,
):
    """
    Test job results
    """

    # Get a token
    response = client.post("/token", json={})
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    token = j["token"]

    # Create the job
    response = client.post(
        "/jobs",
        headers={"API-Key": token},
        json={
            "data": testdata,
            "hexzeros": zeros,
        },
    )
    assert response.status_code == 200, response.data
    j = response.json
    assert j["error"] is None
    job_id = j["job"]["id"]

    # Check if the job is finished
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
    assert j["job"]["final_hash"] == expected_hash, response.data
    assert j["job"]["nonce"] == expected_nonce, response.data
    assert j["job"]["final_hash"][0:zeros] == "0" * zeros
