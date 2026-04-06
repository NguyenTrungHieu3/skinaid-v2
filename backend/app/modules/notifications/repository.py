from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models.notification import Notification
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Notification, db)

    async def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> Tuple[List[Notification], int]:
        filters = [Notification.user_id == user_id]

        if unread_only:
            filters.append(Notification.read_at.is_(None))
        if notification_type:
            filters.append(Notification.notification_type == notification_type)

        count_stmt = (
            select(func.count())
            .select_from(Notification)
            .where(and_(*filters))
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        list_stmt = (
            select(Notification)
            .where(and_(*filters))
            .order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
        )
        items_result = await self.db.execute(list_stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def count_unread(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification: Notification) -> Notification:
        notification.read_at = datetime.now(timezone.utc).replace(tzinfo=None)
        notification.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=now, updated_at=now)
        )
        result = await self.db.execute(stmt)
        return result.rowcount
