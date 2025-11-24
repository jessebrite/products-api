"""Test script to verify TestClient with dependency overrides."""

from conftest import app
from fastapi.testclient import TestClient

from database import get_db


def test_client_setup():
    """Test that TestClient is set up with the test database dependency override."""
    # Check override
    print("get_db in app.dependency_overrides:", get_db in app.dependency_overrides)

    # Create test client
    client = TestClient(app)

    # Try to register a user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200, "Failed to register user"
    assert response.json().get("username") == "testuser"
