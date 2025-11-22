"""Tests for item endpoints."""

import pytest


@pytest.fixture
def auth_token(client):
    """Create user and return auth token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"},
    )
    return response.json()["access_token"]


def test_create_item_successful(client, auth_token):
    """Test successful item creation."""
    response = client.post(
        "/api/v1/items",
        json={"title": "Buy groceries", "description": "Milk, eggs, bread"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk, eggs, bread"
    assert data["is_completed"] is False


def test_create_item_without_auth(client):
    """Test item creation without authentication."""
    response = client.post(
        "/api/v1/items",
        json={"title": "Test item", "description": "Test"},
    )
    assert response.status_code == 401


def test_get_items_empty(client, auth_token):
    """Test getting items when none exist."""
    response = client.get(
        "/api/v1/items",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_items_multiple(client, auth_token):
    """Test getting multiple items."""
    client.post(
        "/api/v1/items",
        json={"title": "Item 1"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    client.post(
        "/api/v1/items",
        json={"title": "Item 2"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    response = client.get(
        "/api/v1/items",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_item_by_id(client, auth_token):
    """Test getting a specific item by ID."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "Specific item", "description": "Test description"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == "Specific item"


def test_get_nonexistent_item(client, auth_token):
    """Test getting a non-existent item."""
    response = client.get(
        "/api/v1/items/999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


def test_update_item_title(client, auth_token):
    """Test updating item title."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "Original title"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Updated title"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"


def test_update_item_completion_status(client, auth_token):
    """Test updating item completion status."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "Task to complete"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"is_completed": True},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_completed"] is True


def test_delete_item_successful(client, auth_token):
    """Test successful item deletion."""
    create_response = client.post(
        "/api/v1/items",
        json={"title": "To delete"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 204


def test_delete_nonexistent_item(client, auth_token):
    """Test deleting a non-existent item."""
    response = client.delete(
        "/api/v1/items/999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404
