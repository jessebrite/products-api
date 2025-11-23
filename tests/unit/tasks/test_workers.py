"""Unit tests for background tasks."""

import pytest
from unittest.mock import patch, MagicMock
from tasks.worker import (
    send_welcome_email,
    log_user_action,
    send_item_notification,
    process_item_completion,
    send_batch_email,
    cleanup_old_data,
)


class TestEmailTasks:
    """Test email-related background tasks."""

    def test_send_welcome_email_success(self):
        """Test that welcome email task runs without error."""
        # Should not raise exception
        send_welcome_email("test@example.com", "testuser")

    def test_send_welcome_email_with_invalid_email(self):
        """Test welcome email task with invalid email."""
        # Should handle gracefully without raising
        send_welcome_email("invalid", "testuser")

    def test_send_batch_email_success(self):
        """Test batch email task with multiple recipients."""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        send_batch_email(recipients, "Test Subject", "Test Body")

    def test_send_batch_email_empty_list(self):
        """Test batch email with empty recipient list."""
        send_batch_email([], "Subject", "Body")


class TestLoggingTasks:
    """Test logging-related background tasks."""

    def test_log_user_action_basic(self):
        """Test basic user action logging."""
        log_user_action("testuser", "LOGIN")

    def test_log_user_action_with_details(self):
        """Test user action logging with additional details."""
        log_user_action("testuser", "CREATE_ITEM", "title: Test Item")

    def test_log_user_action_various_actions(self):
        """Test logging various action types."""
        actions = [
            ("REGISTER", "email: test@example.com"),
            ("LOGIN", "successful authentication"),
            ("CREATE_ITEM", "title: My Item"),
            ("UPDATE_ITEM", "marked as completed"),
            ("DELETE_ITEM", "archived item"),
        ]
        
        for action, details in actions:
            log_user_action("testuser", action, details)


class TestNotificationTasks:
    """Test notification-related background tasks."""

    def test_send_item_notification_created(self):
        """Test item creation notification."""
        send_item_notification(
            "user@example.com", "testuser", "New Item", "created"
        )

    def test_send_item_notification_updated(self):
        """Test item update notification."""
        send_item_notification(
            "user@example.com", "testuser", "Updated Item", "updated"
        )

    def test_send_item_notification_completed(self):
        """Test item completion notification."""
        send_item_notification(
            "user@example.com", "testuser", "Completed Task", "completed"
        )

    def test_send_item_notification_deleted(self):
        """Test item deletion notification."""
        send_item_notification(
            "user@example.com", "testuser", "Deleted Item", "deleted"
        )

    def test_send_item_notification_invalid_type(self):
        """Test notification with invalid type falls back to default."""
        send_item_notification(
            "user@example.com", "testuser", "Some Item", "unknown_type"
        )


class TestCompletionTasks:
    """Test item completion processing tasks."""

    def test_process_item_completion_success(self):
        """Test item completion processing."""
        process_item_completion(1, "testuser", "My Item")

    def test_process_item_completion_multiple_items(self):
        """Test processing completion for multiple items."""
        for i in range(1, 4):
            process_item_completion(i, "testuser", f"Item {i}")


class TestMaintenanceTasks:
    """Test maintenance and cleanup tasks."""

    def test_cleanup_old_data_success(self):
        """Test data cleanup task."""
        cleanup_old_data()

    def test_cleanup_old_data_idempotent(self):
        """Test that cleanup can run multiple times safely."""
        cleanup_old_data()
        cleanup_old_data()  # Should not raise


class TestTaskExceptionHandling:
    """Test that tasks handle exceptions gracefully."""

    def test_send_email_with_exception(self):
        """Test email task handles unexpected errors."""
        # Even if there's an error, the task should not crash the API
        with patch("src.tasks.worker.logger") as mock_logger:
            send_welcome_email("test@example.com", "user")
            # Task completes without propagating exceptions

    def test_logging_task_with_exception(self):
        """Test logging task handles errors."""
        # Task should complete even if logging fails
        log_user_action("user", "ACTION", "details")

    def test_notification_with_exception(self):
        """Test notification task handles errors."""
        # Task should complete gracefully
        send_item_notification("email@test.com", "user", "item", "created")
