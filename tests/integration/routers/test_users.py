"""Integration tests for user endpoints."""

from fastapi.testclient import TestClient

from models import User


class TestUserEndpoints:
    """Test user-related endpoints."""

    def test_get_current_user_success(self, client: TestClient, auth_token: str):
        """Test successful retrieval of current user information."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "is_active" in data
        assert "created_at" in data
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

    def test_get_current_user_not_found(
        self, client: TestClient, auth_token: str, get_db_fixture
    ):
        """Test user not found scenario where authenticated user is deleted from DB."""
        # Delete the user from the database to simulate user not found
        db = get_db_fixture
        user_to_delete = db.query(User).filter(User.username == "testuser").first()
        if user_to_delete:
            db.delete(user_to_delete)
            db.commit()

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test that accessing user info without authentication fails."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 404
        assert "Missing token" in response.json()["detail"]

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test that accessing user info with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 422
        assert "Invalid or expired token" in response.json()["detail"]
