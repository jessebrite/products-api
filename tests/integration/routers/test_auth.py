"""Integration tests for authentication endpoints."""

import os

from fastapi.testclient import TestClient


class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    def test_register_and_login_flow(self, client: TestClient):
        """Test full registration and login flow."""
        # Register a user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secure_password_123",
            },
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["username"] == "john_doe"
        assert user_data["email"] == "john@example.com"

        # Login with the registered user
        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "john_doe", "password": "secure_password_123"},
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "new_user",
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "new_user"
        assert data["email"] == "new@example.com"
        assert data["is_active"] is True
        assert "hashed_password" not in data  # Should not expose hashed password

    def test_register_duplicate_username(self, client: TestClient):
        """Test that registering with duplicate username fails."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate_user",
                "email": "first@example.com",
                "password": "password123",
            },
        )

        # Try to register with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate_user",
                "email": "second@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 409
        assert "Username already exists" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient):
        """Test that registering with duplicate email fails."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "password123",
            },
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 409
        assert "Email already exists" in response.json()["detail"]

    def test_login_success(self, client: TestClient):
        """Test successful login."""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )

        # Login
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        print(f"DB URL====> {os.environ['DATABASE_URL']}")
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent", "password": "wrong_password"},
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "correct_password",
            },
        )

        # Try to login with wrong password
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "wrong_password"},
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
