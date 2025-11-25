def test_docs(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text or "swagger-ui" in response.text.lower()


def test_root_redirect(client):
    response = client.get("/", allow_redirects=False)
    assert response.status_code in (301, 302, 307)
    assert "/docs" in response.headers.get("location", "")


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data or "healthy" in data
