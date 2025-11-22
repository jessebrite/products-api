"""Tests for the CRUD API."""

import pytest


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.fixture
def test_user(client):
    """Create a test user."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
    )
    return response.json()


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"},
    )
    return response.json()["access_token"]


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"


def test_register_duplicate_username(client):
    """Test registration with duplicate username."""
    client.post(
        "/api/v1/auth/register",
        json={"username": "duplicate", "email": "first@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "duplicate", "email": "second@example.com", "password": "password123"},
    )
    assert response.status_code == 400


def test_login(client, test_user):
    """Test user login."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_get_current_user(client, test_user, auth_token):
    """Test getting current user info."""
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_create_item(client, auth_token):
    """Test creating an item."""
    response = client.post(
        "/api/v1/items",
        json={"title": "Test Item", "description": "Test Description"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Item"


def test_get_items(client, auth_token):
    """Test getting items."""
    client.post(
        "/api/v1/items",
        json={"title": "Item 1", "description": "Description 1"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    response = client.get(
        "/api/v1/items", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_item(client, auth_token):
    """Test getting a specific item."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "Test Item", "description": "Test Description"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/items/{item_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_update_item(client, auth_token):
    """Test updating an item."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "Original Title", "description": "Original Description"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Updated Title", "is_completed": True},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["is_completed"] is True


def test_delete_item(client, auth_token):
    """Test deleting an item."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "To Delete", "description": "Delete this"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/items/{item_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(
        f"/api/v1/items/{item_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 404
