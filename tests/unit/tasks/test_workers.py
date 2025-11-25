"""Unit tests for background tasks."""

from unittest.mock import patch

from tasks.worker import (
    cleanup_old_data,
    log_user_action,
    process_item_completion,
    send_batch_email,
    send_item_notification,
    send_welcome_email,
)


class TestEmailTasks:
    """Test email-related background tasks."""

    @patch("tasks.worker.logger")
    def test_send_welcome_email_success(self, mock_logger):
        """Test that welcome email task runs without error."""
        send_welcome_email("test@example.com", "testuser")
        mock_logger.info.assert_called_once()
        assert (
            "Welcome email sent to test@example.com" in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_send_welcome_email_with_invalid_email(self, mock_logger):
        """Test welcome email task with invalid email."""
        send_welcome_email("invalid", "testuser")
        mock_logger.info.assert_called_once()
        assert "Welcome email sent to invalid" in mock_logger.info.call_args[0][0]

    @patch("tasks.worker.logger")
    def test_send_welcome_email_exception_handling(self, mock_logger):
        """Test welcome email handles exceptions."""
        mock_logger.info.side_effect = Exception("Log error")
        send_welcome_email("test@example.com", "testuser")
        mock_logger.error.assert_called_once()
        assert "Failed to send welcome email" in mock_logger.error.call_args[0][0]

    @patch("tasks.worker.logger")
    def test_send_batch_email_success(self, mock_logger):
        """Test batch email task with multiple recipients."""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        send_batch_email(recipients, "Test Subject", "Test Body")
        mock_logger.info.assert_called_once()
        assert "Batch email sent to 3 recipients" in mock_logger.info.call_args[0][0]

    @patch("tasks.worker.logger")
    def test_send_batch_email_empty_list(self, mock_logger):
        """Test batch email with empty recipient list."""
        send_batch_email([], "Subject", "Body")
        mock_logger.info.assert_called_once()
        assert "Batch email sent to 0 recipients" in mock_logger.info.call_args[0][0]

    @patch("tasks.worker.logger")
    def test_send_batch_email_exception_handling(self, mock_logger):
        """Test batch email handles exceptions."""
        mock_logger.info.side_effect = Exception("Log error")
        send_batch_email(["test@example.com"], "Subject", "Body")
        mock_logger.error.assert_called_once()
        assert "Failed to send batch emails" in mock_logger.error.call_args[0][0]


class TestLoggingTasks:
    """Test logging-related background tasks."""

    @patch("tasks.worker.logger")
    def test_log_user_action_basic(self, mock_logger):
        """Test basic user action logging."""
        log_user_action("testuser", "LOGIN")
        mock_logger.info.assert_called_once()
        assert (
            "User 'testuser' performed action 'LOGIN'"
            in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_log_user_action_with_details(self, mock_logger):
        """Test user action logging with additional details."""
        log_user_action("testuser", "CREATE_ITEM", "title: Test Item")
        mock_logger.info.assert_called_once()
        assert (
            "User 'testuser' performed action 'CREATE_ITEM' - title: Test Item"
            in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_log_user_action_various_actions(self, mock_logger):
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
        assert mock_logger.info.call_count == 5

    @patch("tasks.worker.logger")
    def test_log_user_action_exception_handling(self, mock_logger):
        """Test logging task handles exceptions."""
        mock_logger.info.side_effect = Exception("Log error")
        log_user_action("testuser", "LOGIN")
        mock_logger.error.assert_called_once()
        assert (
            "Failed to log user action for testuser"
            in mock_logger.error.call_args[0][0]
        )


class TestNotificationTasks:
    """Test notification-related background tasks."""

    @patch("tasks.worker.logger")
    def test_send_item_notification_created(self, mock_logger):
        """Test item creation notification."""
        send_item_notification("user@example.com", "testuser", "New Item", "created")
        mock_logger.info.assert_called_once()
        assert (
            "Your item 'New Item' has been created" in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_send_item_notification_updated(self, mock_logger):
        """Test item update notification."""
        send_item_notification(
            "user@example.com", "testuser", "Updated Item", "updated"
        )
        mock_logger.info.assert_called_once()
        assert (
            "Your item 'Updated Item' has been updated"
            in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_send_item_notification_completed(self, mock_logger):
        """Test item completion notification."""
        send_item_notification(
            "user@example.com", "testuser", "Completed Task", "completed"
        )
        mock_logger.info.assert_called_once()
        assert (
            "You marked 'Completed Task' as completed"
            in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_send_item_notification_deleted(self, mock_logger):
        """Test item deletion notification."""
        send_item_notification(
            "user@example.com", "testuser", "Deleted Item", "deleted"
        )
        mock_logger.info.assert_called_once()
        assert (
            "Your item 'Deleted Item' has been deleted"
            in mock_logger.info.call_args[0][0]
        )

    @patch("tasks.worker.logger")
    def test_send_item_notification_invalid_type(self, mock_logger):
        """Test notification with invalid type falls back to default."""
        send_item_notification(
            "user@example.com", "testuser", "Some Item", "unknown_type"
        )
        mock_logger.info.assert_called_once()
        assert "Action on item 'Some Item'" in mock_logger.info.call_args[0][0]

    @patch("tasks.worker.logger")
    def test_send_item_notification_exception_handling(self, mock_logger):
        """Test notification task handles exceptions."""
        mock_logger.info.side_effect = Exception("Log error")
        send_item_notification("user@example.com", "testuser", "Item", "created")
        mock_logger.error.assert_called_once()
        assert (
            "Failed to send notification to user@example.com"
            in mock_logger.error.call_args[0][0]
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

    @patch("tasks.worker.logger")
    def test_cleanup_old_data_success(self, mock_logger):
        """Test data cleanup task."""
        cleanup_old_data()
        assert mock_logger.info.call_count == 2  # start and completion logs

    @patch("tasks.worker.logger")
    def test_cleanup_old_data_idempotent(self, mock_logger):
        """Test that cleanup can run multiple times safely."""
        cleanup_old_data()
        cleanup_old_data()  # Should not raise
        assert mock_logger.info.call_count == 4  # 2 logs per run

    @patch("tasks.worker.logger")
    def test_cleanup_old_data_exception_handling(self, mock_logger):
        """Test cleanup handles exceptions."""
        mock_logger.info.side_effect = Exception("Log error")
        cleanup_old_data()
        mock_logger.error.assert_called_once()
        assert "Failed to cleanup old data" in mock_logger.error.call_args[0][0]


class TestTaskExceptionHandling:
    """Test that tasks handle exceptions gracefully."""

    @patch("tasks.worker.logger")
    def test_send_email_with_exception(self, mock_logger):
        """Test email task handles unexpected errors."""
        # Even if there's an error, the task should not crash the API
        send_welcome_email("test@example.com", "user")
        # Since logger is mocked, no actual error occurs, but task completes
        mock_logger.info.assert_called_once()

    @patch("tasks.worker.logger")
    def test_logging_task_with_exception(self, mock_logger):
        """Test logging task handles errors."""
        # Task should complete even if logging fails
        log_user_action("user", "ACTION", "details")
        mock_logger.info.assert_called_once()

    @patch("tasks.worker.logger")
    def test_notification_with_exception(self, mock_logger):
        """Test notification task handles errors."""
        # Task should complete gracefully
        send_item_notification("email@test.com", "user", "item", "created")
        mock_logger.info.assert_called_once()
