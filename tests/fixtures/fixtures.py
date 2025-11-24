"""Shared fixtures for tests."""

import pytest


@pytest.fixture
def auth_token(client):
    """Create a test user and return their auth token."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    # Login and get token
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def test_user_credentials():
    """Return test user credentials."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
    }


@pytest.fixture
def admin_user_credentials():
    """Return admin user credentials."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin_password_123",
    }
