def test_healthz_matches_contract(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readyz_matches_contract(client):
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ready",
        "checks": {
            "database": "ok",
        },
    }