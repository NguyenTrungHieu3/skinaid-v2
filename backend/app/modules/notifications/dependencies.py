from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.service import NotificationService


async def get_notification_repository(
    db: AsyncSession = Depends(get_db),
) -> NotificationRepository:
    return NotificationRepository(db)


async def get_notification_service(
    repository: NotificationRepository = Depends(get_notification_repository),
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(repository, db)


NotificationRepo = Annotated[NotificationRepository, Depends(get_notification_repository)]
NotificationSvc = Annotated[NotificationService, Depends(get_notification_service)]
