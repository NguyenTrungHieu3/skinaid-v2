from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models.device_session import DeviceSession
from app.shared.base_repository import BaseRepository


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DeviceSessionRepository(BaseRepository[DeviceSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(DeviceSession, db)

    async def get_by_user_device(
        self, user_id: UUID, device_id: str
    ) -> Optional[DeviceSession]:
        return await self.get_one(
            DeviceSession.user_id == user_id,
            DeviceSession.device_id == device_id,
        )

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        only_active: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[DeviceSession]:
        stmt = select(DeviceSession).where(DeviceSession.user_id == user_id)
        if only_active:
            stmt = stmt.where(DeviceSession.is_active == True)  # noqa: E712
        stmt = stmt.order_by(DeviceSession.last_activity_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_by_user(self, user_id: UUID, *, only_active: bool = True) -> int:
        stmt = select(func.count()).select_from(DeviceSession).where(
            DeviceSession.user_id == user_id
        )
        if only_active:
            stmt = stmt.where(DeviceSession.is_active == True)  # noqa: E712
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def touch_activity(self, entity: DeviceSession) -> DeviceSession:
        entity.last_activity_at = _now()
        entity.updated_at = _now()
        await self.db.flush()
        return entity
