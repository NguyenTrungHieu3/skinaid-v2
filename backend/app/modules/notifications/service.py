from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.exceptions import (
    NotificationForbiddenError,
    NotificationNotFoundError,
)
from app.modules.notifications.models.notification import Notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas.api import (
    BroadcastNotificationResponse,
    CreateNotificationRequest,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
        db: AsyncSession,
    ) -> None:
        self._repository = repository
        self._db = db

    async def get_notification_by_id(self, notification_id: UUID) -> NotificationResponse:
        """Lấy thông tin chi tiết một notification theo ID."""
        notif = await self._repository.get_by_id(notification_id)
        if not notif:
            raise NotFoundException(message="Notification not found")
        return NotificationResponse.model_validate(notif)

    async def list_notifications(
        self,
        user_id: Optional[UUID],
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> NotificationListResponse:
        items, total = await self._repository.get_user_notifications(
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            notification_type=notification_type,
        )
        if user_id is not None:
            unread_count = await self._repository.count_unread(user_id)
        else:
            unread_count = await self._repository.count_unread_all()
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            unread_count=unread_count,
        )

    async def get_unread_count(self, user_id: UUID) -> UnreadCountResponse:
        count = await self._repository.count_unread(user_id)
        return UnreadCountResponse(unread_count=count)

    async def mark_read(
        self, notification_id: UUID, current_user_id: UUID, is_admin: bool = False
    ) -> NotificationResponse:
        notification = await self._repository.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError(str(notification_id))
        if notification.user_id != current_user_id and not is_admin:
            raise NotificationForbiddenError()

        updated = await self._repository.mark_as_read(notification)
        return NotificationResponse.model_validate(updated)

    async def mark_all_read(self, user_id: UUID) -> dict:
        updated_count = await self._repository.mark_all_read(user_id)
        return {"updated_count": updated_count}

    async def delete(self, notification_id: UUID, current_user_id: UUID, is_admin: bool = False) -> None:
        notification = await self._repository.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError(str(notification_id))
        if notification.user_id != current_user_id and not is_admin:
            raise NotificationForbiddenError()

        await self._repository.delete(notification)

    async def create_for_user(
        self, request: CreateNotificationRequest
    ) -> NotificationResponse:
        """Tạo 1 notification cho user cụ thể (recipient_type='specific')."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        notification = Notification(
            user_id=request.user_id,
            title=request.title,
            body=request.body,
            notification_type=request.notification_type,
            data=request.data,
            action_url=request.action_url,
            image_url=request.image_url,
            priority=request.priority,
            status="sent",
            sent_at=now,
        )
        created = await self._repository.create(notification)
        await self._db.refresh(created)
        return NotificationResponse.model_validate(created)

    async def create_broadcast(
        self, request: CreateNotificationRequest
    ) -> BroadcastNotificationResponse:
        """Gửi notification đến TẤT CẢ user đang active (recipient_type='all')."""
        user_ids = await self._repository.get_all_active_user_ids()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        count = 0
        for uid in user_ids:
            notification = Notification(
                user_id=uid,
                title=request.title,
                body=request.body,
                notification_type=request.notification_type,
                data=request.data,
                action_url=request.action_url,
                image_url=request.image_url,
                priority=request.priority,
                status="sent",
                sent_at=now,
            )
            await self._repository.create(notification)
            count += 1

        await self._db.flush()
        logger.info(
            "[NotificationService] broadcast sent to %d active users. title=%r",
            count,
            request.title,
        )
        return BroadcastNotificationResponse(
            sent_count=count,
            title=request.title,
            notification_type=request.notification_type,
        )

    async def create_analysis_complete(
        self,
        user_id: UUID,
        analysis_id: str,
        wound_type: str,
        severity: str,
    ) -> Notification:
        """Public hook for AI module — call fire-and-forget after B4 completes."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        severity_display = {"mild": "Nhẹ", "moderate": "Trung bình", "severe": "Nặng"}.get(
            severity.lower(), severity
        )
        wound_display = {
            "abrasion": "Trầy xước", "bruise": "Bầm tím", "burn": "Bỏng",
            "cut": "Vết cắt", "acne": "Mụn trứng cá", "fungal": "Nấm da",
            "psoriasis": "Vảy nến",
        }.get(wound_type.lower(), wound_type)

        notification = Notification(
            user_id=user_id,
            title="Phân tích vết thương hoàn tất",
            body=f"Đã phát hiện {wound_display} mức độ {severity_display}. Nhấn để xem hướng dẫn sơ cứu.",
            notification_type="analysis_complete",
            data={"analysis_id": analysis_id, "wound_type": wound_type, "severity": severity},
            action_url=f"/analysis-result/{analysis_id}",
            priority="high",
            status="sent",
            sent_at=now,
        )
        created = await self._repository.create(notification)
        logger.info(
            "[NotificationService] analysis_complete notification created "
            "(user_id=%s, analysis_id=%s).",
            user_id,
            analysis_id,
        )
        return created
