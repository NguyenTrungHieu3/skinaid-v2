"""
Dependency-injection factories for the notifications module.
"""
from app.modules.notifications.service import NotificationService


def get_notification_service() -> NotificationService:
    """Return a NotificationService instance (currently a stub)."""
    return NotificationService()
