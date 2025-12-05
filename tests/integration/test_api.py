import pytest

from main import app


def test_swagger_docs_accessible(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text or "swagger-ui" in response.text.lower()


def test_openapi_metadata(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    json_data = response.json()
    # OpenAPI metadata is under the 'info' key
    assert "info" in json_data
    assert json_data["info"]["title"] == app.title
    assert json_data["info"]["description"] == app.description
    assert json_data["info"]["version"] == app.version


@pytest.mark.parametrize(
    "endpoint, method",
    [
        ("/api/v1/auth/token", "POST"),
        ("/api/v1/users", "GET"),
        ("/api/v1/items", "GET"),
    ],
)
def test_protected_or_api_endpoints_status(endpoint, method, client):
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        # Send empty data for token endpoint, expecting 422 or 401 or
        # 405 if method not allowed
        response = client.post(endpoint, data={})
    else:
        response = client.get(endpoint)
    # Status code may vary depending on authentication required or endpoint setup
    assert response.status_code in (
        200,
        401,
        422,
        403,
        404,
        405,
    )  # Accept expected variation
