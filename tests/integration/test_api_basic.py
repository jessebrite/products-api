"""Integration tests for general API endpoints."""


class TestAPIBasics:
    """Test basic API functionality."""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema availability."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data

    def test_get_current_user(self, client, auth_token):
        """Test getting current user info."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

    def test_swagger_docs_available(self, client):
        """Test that Swagger documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_docs_available(self, client):
        """Test that ReDoc documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
