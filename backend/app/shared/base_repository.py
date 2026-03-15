import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Generic, Optional, Sequence, TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):

    def __init__(self, model: type[T], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        return await self.db.get(self.model, entity_id)

    async def get_one(
        self,
        *filters: Any,
    ) -> Optional[T]:
        statement = select(self.model).where(*filters)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_one_by_stmt(self, statement: Any) -> Optional[T]:
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_many(
        self,
        *filters: Any,
        skip: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> Sequence[T]:
        statement = select(self.model).where(
            *filters).offset(skip).limit(limit)
        if order_by is not None:
            statement = statement.order_by(order_by)
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def get_many_by_stmt(self, statement: Any) -> Sequence[T]:
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def count(self, *filters: Any) -> int:
        statement = select(func.count()).select_from(
            self.model).where(*filters)
        result = await self.db.execute(statement)
        return result.scalar_one()

    async def create(self, entity: T) -> T:
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: T, data: dict[str, Any]) -> T:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self.db.delete(entity)
        await self.db.flush()

    async def soft_delete(
        self,
        entity: T,
        *,
        field_name: str = "is_deleted",
    ) -> T:
        if not hasattr(entity, field_name):
            raise AttributeError(
                f"Model {self.model.__name__} không có field '{field_name}'"
            )
        setattr(entity, field_name, True)
        if hasattr(entity, "updated_at"):
            entity.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity
