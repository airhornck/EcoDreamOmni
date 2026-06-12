


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "EcoDreamOmni API is running"
