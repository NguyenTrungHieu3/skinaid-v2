"""
Notification Service — stub implementation.

This module provides a minimal NotificationService that logs notification
intents but does not actually deliver them (e.g. via push/email).

Replace with a real implementation when ready.
"""
import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class NotificationService:
    """Stub notification service.

    All public methods are intentionally no-ops so that callers
    (e.g. ImageProcessingService) can depend on the service without
    breaking when the notification infrastructure is not yet configured.
    """

    async def create_analysis_complete(
        self,
        user_id: UUID,
        analysis_id: str,
        wound_type: str = "",
        severity: str = "",
    ) -> None:
        """Called after a wound analysis completes successfully."""
        logger.info(
            "[NotificationService] Analysis complete notification "
            "(stub) — user=%s analysis=%s wound=%s severity=%s",
            user_id, analysis_id, wound_type, severity,
        )

    async def send(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str = "general",
        data: Optional[dict] = None,
    ) -> None:
        """Generic send — currently a no-op stub."""
        logger.info(
            "[NotificationService] send (stub) — user=%s type=%s title=%s",
            user_id, notification_type, title,
        )
