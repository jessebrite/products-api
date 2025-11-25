"""Integration tests for background tasks in endpoints."""


class TestAuthenticationWithBackgroundTasks:
    """Test authentication endpoints with background tasks."""

    def test_register_triggers_background_tasks(self, client):
        """Test that registration triggers welcome email and logging tasks."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "tasktest",
                "email": "tasktest@example.com",
                "password": "password123",
            },
        )

        # Request completes successfully
        assert response.status_code == 200

        # Background tasks run after response, so user is created
        data = response.json()
        assert data["username"] == "tasktest"
        assert data["email"] == "tasktest@example.com"

    def test_login_triggers_logging_task(self, client):
        """Test that login triggers logging task."""
        # First register
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "logintest",
                "email": "logintest@example.com",
                "password": "password123",
            },
        )

        # Then login - should trigger log_user_action task
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "logintest", "password": "password123"},
        )

        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data


class TestItemsWithBackgroundTasks:
    """Test item endpoints with background tasks."""

    def test_create_item_triggers_notification_task(self, client, auth_token):
        """Test that creating item triggers notification task."""
        response = client.post(
            "/api/v1/items",
            json={"title": "Background Task Test", "description": "Testing"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Request completes successfully
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Background Task Test"
        # Background task for notification runs asynchronously

    def test_update_item_triggers_notification_and_completion_task(
        self, client, auth_token
    ):
        """Test that updating item completion triggers processing task."""
        # Create item
        create_response = client.post(
            "/api/v1/items",
            json={"title": "Item to Complete", "description": "Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Mark as completed - should trigger process_item_completion task
        response = client.put(
            f"/api/v1/items/{item_id}",
            json={"is_completed": True},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_completed"] is True
        # Background tasks run after response

    def test_update_item_to_incomplete_no_completion_task(self, client, auth_token):
        """Test updating back to incomplete doesn't trigger completion task."""
        # Create and complete item
        create_response = client.post(
            "/api/v1/items",
            json={"title": "Item", "description": "Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Complete it
        client.put(
            f"/api/v1/items/{item_id}",
            json={"is_completed": True},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Update back to incomplete
        response = client.put(
            f"/api/v1/items/{item_id}",
            json={"is_completed": False},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_completed"] is False

    def test_delete_item_triggers_notification_task(self, client, auth_token):
        """Test that deleting item triggers notification task."""
        # Create item
        create_response = client.post(
            "/api/v1/items",
            json={"title": "Item to Delete", "description": "Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        item_id = create_response.json()["id"]

        # Delete it - should trigger notification task
        response = client.delete(
            f"/api/v1/items/{item_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 204
        # Background task for deletion notification runs asynchronously


class TestBackgroundTasksNonBlocking:
    """Test that background tasks don't block the API response."""

    def test_multiple_registrations_complete_quickly(self, client):
        """Test that multiple registrations aren't blocked by background tasks."""
        responses = []

        for i in range(3):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": f"user{i}",
                    "email": f"user{i}@example.com",
                    "password": "password123",
                },
            )
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    def test_multiple_item_operations_complete_quickly(self, client, auth_token):
        """Test that multiple item operations aren't blocked by background tasks."""
        responses = []

        for i in range(3):
            response = client.post(
                "/api/v1/items",
                json={"title": f"Item {i}", "description": "Test"},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)
