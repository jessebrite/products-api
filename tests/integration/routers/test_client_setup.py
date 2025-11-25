"""Test script to verify TestClient with dependency overrides."""


def test_client_setup(client):
    """Test that TestClient is set up with the test database dependency override."""
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
