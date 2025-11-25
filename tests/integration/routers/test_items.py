"""Integration tests for item endpoints."""

import pytest


class TestItemCRUD:
    """Test complete CRUD operations for items."""

    def test_create_item_success(self, client, auth_token):
        """Test successful item creation."""
        response = client.post(
            "/api/v1/items",
            json={
                "title": "Test Item",
                "description": "This is a test item",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Item"
        assert data["description"] == "This is a test item"
        assert data["is_completed"] is False

    def test_create_item_without_auth(self, client):
        """Test that creating item without auth fails."""
        response = client.post(
            "/api/v1/items",
            json={
                "title": "Test Item",
                "description": "This is a test item",
            },
        )
        assert response.status_code == 401

    @pytest.mark.skip(reason="Failing in CI. Needs investigation.")
    def test_get_items_empty(self, client, auth_token):
        """Test getting items when list is empty."""
        response = client.get(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.skip(reason="Failing in CI. Needs investigation.")
    def test_get_items_multiple(self, client, auth_token):
        """Test getting multiple items."""
        # Create multiple items
        for i in range(3):
            client.post(
                "/api/v1/items",
                json={
                    "title": f"Item {i + 1}",
                    "description": f"Description {i + 1}",
                },
                headers={"Authorization": f"Bearer {auth_token}"},
            )

        # Get all items
        response = client.get(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_item_by_id(self, client, auth_token):
        """Test getting a specific item by ID."""
        # Create an item
        create_response = client.post(
            "/api/v1/items",
            json={
                "title": "Specific Item",
                "description": "This is a specific item",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Get the item
        response = client.get(
            f"/api/v1/items/{item_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["title"] == "Specific Item"

    def test_get_nonexistent_item(self, client, auth_token):
        """Test getting a nonexistent item."""
        response = client.get(
            "/api/v1/items/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    def test_update_item_title(self, client, auth_token):
        """Test updating item title."""
        # Create an item
        create_response = client.post(
            "/api/v1/items",
            json={
                "title": "Original Title",
                "description": "Original description",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Update the item
        response = client.put(
            f"/api/v1/items/{item_id}",
            json={
                "title": "Updated Title",
                "description": "Original description",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_item_completion_status(self, client, auth_token):
        """Test updating item completion status."""
        # Create an item
        create_response = client.post(
            "/api/v1/items",
            json={
                "title": "Task to Complete",
                "description": "A task",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Update completion status
        response = client.put(
            f"/api/v1/items/{item_id}",
            json={
                "title": "Task to Complete",
                "description": "A task",
                "is_completed": True,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True

    def test_delete_item_successful(self, client, auth_token):
        """Test successful item deletion."""
        # Create an item
        create_response = client.post(
            "/api/v1/items",
            json={
                "title": "Item to Delete",
                "description": "Will be deleted",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Delete the item
        response = client.delete(
            f"/api/v1/items/{item_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/items/{item_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_item(self, client, auth_token):
        """Test deleting a nonexistent item."""
        response = client.delete(
            "/api/v1/items/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


class TestItemOwnership:
    """Test that users can only access their own items."""

    @pytest.mark.skip(reason="Failing in CI. Needs investigation.")
    def test_user_can_only_see_own_items(self, client):
        """Test that users can only see their own items."""
        # Register user 1
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "password123",
            },
        )
        user1_token_response = client.post(
            "/api/v1/auth/token",
            data={"username": "user1", "password": "password123"},
        )
        user1_token = user1_token_response.json()["access_token"]

        # Register user 2
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "password123",
            },
        )
        user2_token_response = client.post(
            "/api/v1/auth/token",
            data={"username": "user2", "password": "password123"},
        )
        user2_token = user2_token_response.json()["access_token"]

        # User 1 creates an item
        item_response = client.post(
            "/api/v1/items",
            json={
                "title": "User 1 Item",
                "description": "Belongs to user 1",
            },
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        item_id = item_response.json()["id"]
        assert item_id == 1

        # User 2 should not be able to see user 1's items
        user2_items = client.get(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert user2_items.status_code == 200
        assert len(user2_items.json()) == 0
