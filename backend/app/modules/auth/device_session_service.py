import logging
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.exceptions import (
    DeviceForbiddenError,
    DeviceSessionNotFoundError,
)
from app.modules.auth.models.device_session import DeviceSession
from app.modules.auth.repository.device_session_repository import DeviceSessionRepository
from app.modules.auth.schemas.device_session import (
    DeviceRegisterRequest,
    DeviceUpdateRequest,
    SyncStatusUpdateRequest,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DeviceSessionService:
    def __init__(self, repo: DeviceSessionRepository, db: AsyncSession) -> None:
        self.repo = repo
        self.db = db

    async def register_device(
        self, user_id: UUID, payload: DeviceRegisterRequest
    ) -> DeviceSession:
        existing = await self.repo.get_by_user_device(user_id, payload.device_id)
        if existing:
            data = payload.model_dump(exclude_unset=True, exclude={"device_id"})
            data["is_active"] = True
            data["last_activity_at"] = _now()
            entity = await self.repo.update(existing, data)
        else:
            entity = DeviceSession(
                user_id=user_id,
                device_id=payload.device_id,
                platform=payload.platform,
                app_version=payload.app_version,
                os_version=payload.os_version,
                device_model=payload.device_model,
                device_name=payload.device_name,
                push_token=payload.push_token,
                push_enabled=payload.push_enabled,
            )
            entity = await self.repo.create(entity)
        return entity

    async def upsert_on_login(
        self,
        user_id: UUID,
        *,
        device_id: Optional[str],
        platform: Optional[str],
        app_version: Optional[str] = None,
        os_version: Optional[str] = None,
        device_model: Optional[str] = None,
        device_name: Optional[str] = None,
        push_token: Optional[str] = None,
    ) -> Optional[DeviceSession]:
        if not device_id or not platform:
            return None
        existing = await self.repo.get_by_user_device(user_id, device_id)
        if existing:
            update_data: dict = {
                "platform": platform,
                "is_active": True,
                "last_activity_at": _now(),
            }
            if app_version is not None:
                update_data["app_version"] = app_version
            if os_version is not None:
                update_data["os_version"] = os_version
            if device_model is not None:
                update_data["device_model"] = device_model
            if device_name is not None:
                update_data["device_name"] = device_name
            if push_token is not None:
                update_data["push_token"] = push_token
            return await self.repo.update(existing, update_data)
        entity = DeviceSession(
            user_id=user_id,
            device_id=device_id,
            platform=platform,
            app_version=app_version,
            os_version=os_version,
            device_model=device_model,
            device_name=device_name,
            push_token=push_token,
        )
        return await self.repo.create(entity)

    async def list_user_devices(
        self, user_id: UUID, *, only_active: bool = True, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[DeviceSession], int]:
        items = await self.repo.list_by_user(
            user_id, only_active=only_active, skip=skip, limit=limit
        )
        total = await self.repo.count_by_user(user_id, only_active=only_active)
        return items, total

    async def get_device(self, session_id: UUID, user_id: UUID) -> DeviceSession:
        entity = await self.repo.get_by_id(session_id)
        if not entity:
            raise DeviceSessionNotFoundError(str(session_id))
        if entity.user_id != user_id:
            raise DeviceForbiddenError()
        return entity

    async def update_device(
        self, session_id: UUID, user_id: UUID, payload: DeviceUpdateRequest
    ) -> DeviceSession:
        entity = await self.get_device(session_id, user_id)
        data = payload.model_dump(exclude_unset=True)
        data["last_activity_at"] = _now()
        return await self.repo.update(entity, data)

    async def update_sync_status(
        self, session_id: UUID, user_id: UUID, payload: SyncStatusUpdateRequest
    ) -> DeviceSession:
        entity = await self.get_device(session_id, user_id)
        data = payload.model_dump(exclude_unset=True)
        if "last_sync_at" not in data:
            data["last_sync_at"] = _now()
        data["last_activity_at"] = _now()
        return await self.repo.update(entity, data)

    async def mark_trusted(self, session_id: UUID, is_trusted: bool = True) -> DeviceSession:
        entity = await self.repo.get_by_id(session_id)
        if not entity:
            raise DeviceSessionNotFoundError(str(session_id))
        data: dict = {"is_trusted": is_trusted}
        if is_trusted:
            data["last_trusted_at"] = _now()
        return await self.repo.update(entity, data)

    async def revoke_device(self, session_id: UUID, user_id: UUID) -> DeviceSession:
        entity = await self.get_device(session_id, user_id)
        return await self.repo.update(
            entity, {"is_active": False, "last_activity_at": _now()}
        )

    async def delete_device(self, session_id: UUID, user_id: UUID) -> None:
        entity = await self.get_device(session_id, user_id)
        await self.repo.delete(entity)
