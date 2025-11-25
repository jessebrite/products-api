"""Background tasks for async operations.

Background tasks run after the response is sent to the client, allowing
long-running operations without blocking the user's request.

Example:
    from fastapi import BackgroundTasks
    from tasks import send_welcome_email

    @app.post("/register")
    def register(user: UserCreate, background_tasks: BackgroundTasks):
        # Create user
        new_user = User(...)
        db.add(new_user)
        db.commit()

        # Add background task - runs after response is sent
        background_tasks.add_task(send_welcome_email, user.email, user.username)

        return new_user
"""

import logging
from datetime import datetime
from typing import Optional

# Configure logging for tasks
logger = logging.getLogger("tasks")
logger.setLevel(logging.INFO)


def send_welcome_email(email: str, username: str) -> None:
    """Send welcome email to newly registered user.

    Args:
        email: User's email address
        username: User's username
    """
    try:
        # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
        # For now, just log the operation
        log_message = (
            f"📧 [TASK] Welcome email sent to {email} (user: {username}) "
            f"at {datetime.utcnow().isoformat()}"
        )
        logger.info(log_message)

        # Simulated email sending logic:
        # - Connect to email service
        # - Load email template
        # - Substitute user variables
        # - Send email
        # - Log success/failure

    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")


def log_user_action(username: str, action: str, details: Optional[str] = None) -> None:
    """Log user action for audit trail.

    Args:
        username: Username who performed action
        action: Action performed (e.g., "LOGIN", "CREATE_ITEM", "DELETE_ITEM")
        details: Additional details about the action
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        details_str = f" - {details}" if details else ""
        log_message = (
            f"📝 [AUDIT] User '{username}' performed action '{action}'{details_str} "
            f"at {timestamp}"
        )
        logger.info(log_message)

        # TODO: Store in audit log database table or external logging service
        # - Insert into audit_logs table
        # - Send to Elasticsearch/Splunk
        # - Archive old logs

    except Exception as e:
        logger.error(f"Failed to log user action for {username}: {e}")


def send_item_notification(
    recipient_email: str,
    recipient_username: str,
    item_title: str,
    notification_type: str = "created",
) -> None:
    """Send notification about item activity to user.

    Args:
        recipient_email: Recipient's email
        recipient_username: Recipient's username
        item_title: Title of the item
        notification_type: Type of notification (created, updated, completed, deleted)
    """
    try:
        notification_messages = {
            "created": f"Your item '{item_title}' has been created",
            "updated": f"Your item '{item_title}' has been updated",
            "completed": f"You marked '{item_title}' as completed",
            "deleted": f"Your item '{item_title}' has been deleted",
        }

        message = notification_messages.get(
            notification_type, f"Action on item '{item_title}'"
        )

        log_msg = (
            f"🔔 [TASK] Notification sent to {recipient_email} "
            f"({recipient_username}): {message} "
            f"at {datetime.utcnow().isoformat()}"
        )
        logger.info(log_msg)

        # TODO: Send actual notification
        # - Email notification
        # - Push notification
        # - In-app notification
        # - SMS notification

    except Exception as e:
        logger.error(f"Failed to send notification to {recipient_email}: {e}")


def process_item_completion(item_id: int, username: str, item_title: str) -> None:
    """Process item completion (can trigger other tasks).

    Args:
        item_id: ID of the completed item
        username: Username who completed it
        item_title: Title of the item
    """
    try:
        log_message = (
            f"✅ [TASK] Item #{item_id} '{item_title}' marked as completed by "
            f" '{username}' at {datetime.utcnow().isoformat()}"
        )
        logger.info(log_message)

        # TODO: Add logic for item completion
        # - Update item completion statistics
        # - Award user achievement/badge
        # - Send congratulation email
        # - Update user streak
        # - Trigger related notifications

    except Exception as e:
        logger.error(f"Failed to process item completion for item {item_id}: {e}")


def send_batch_email(recipient_list: list, subject: str, body: str) -> None:
    """Send batch email to multiple recipients.

    Args:
        recipient_list: List of email addresses
        subject: Email subject
        body: Email body
    """
    try:
        log_message = (
            f"📧 [TASK] Batch email sent to {len(recipient_list)} recipients "
            f"(Subject: '{subject}') at {datetime.utcnow().isoformat()}"
        )
        logger.info(log_message)

        # TODO: Send actual batch emails
        # - Use SendGrid, AWS SES, or similar
        # - Handle failures gracefully
        # - Log delivery status

    except Exception as e:
        logger.error(f"Failed to send batch emails: {e}")


def cleanup_old_data() -> None:
    """Clean up old/deleted data periodically.

    This task can be scheduled to run periodically (e.g., daily).
    """
    try:
        log_message = (
            f"🧹 [TASK] Data cleanup started at {datetime.utcnow().isoformat()}"
        )
        logger.info(log_message)

        # TODO: Add cleanup logic
        # - Delete old logs
        # - Archive old completed items
        # - Clean up temporary files
        # - Optimize database

        cleanup_message = (
            f"✓ [TASK] Data cleanup completed at {datetime.utcnow().isoformat()}"
        )
        logger.info(cleanup_message)

    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")


__all__ = [
    "send_welcome_email",
    "log_user_action",
    "send_item_notification",
    "process_item_completion",
    "send_batch_email",
    "cleanup_old_data",
]
