"""
BaseRepository — Repository gốc với các phương thức CRUD generic.

Sử dụng SQLModel ORM, tất cả repositories kế thừa từ class này.
"""

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
    """Repository gốc cung cấp các thao tác CRUD cơ bản."""

    def __init__(self, model: type[T], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    # ── READ ──────────────────────────────────────────────

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        """Lấy entity theo primary key."""
        return await self.db.get(self.model, entity_id)

    async def get_one(
        self,
        *filters: Any,
    ) -> Optional[T]:
        """
        Lấy 1 entity theo filters.

        Args:
            *filters: Điều kiện SQLAlchemy (vd: User.email == "x@y.com")
        """
        statement = select(self.model).where(*filters)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_many(
        self,
        *filters: Any,
        skip: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> Sequence[T]:
        """
        Lấy danh sách entities với filter + pagination.

        Args:
            *filters: Điều kiện SQLAlchemy
            skip: Số bản ghi bỏ qua
            limit: Số bản ghi tối đa trả về
            order_by: Cột sắp xếp (vd: User.created_at.desc())
        """
        statement = select(self.model).where(
            *filters).offset(skip).limit(limit)
        if order_by is not None:
            statement = statement.order_by(order_by)
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def count(self, *filters: Any) -> int:
        """Đếm số lượng entities theo filters."""
        statement = select(func.count()).select_from(
            self.model).where(*filters)
        result = await self.db.execute(statement)
        return result.scalar_one()

    # ── CREATE ────────────────────────────────────────────

    async def create(self, entity: T) -> T:
        """
        Thêm entity mới vào database.

        Dùng flush() thay commit() để caller kiểm soát transaction.
        """
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    # ── UPDATE ────────────────────────────────────────────

    async def update(self, entity: T, data: dict[str, Any]) -> T:
        """
        Cập nhật entity với dữ liệu từ dict.

        Args:
            entity: Entity cần cập nhật (đã load từ DB)
            data: Dict chứa các field cần cập nhật
        """
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    # ── DELETE ────────────────────────────────────────────

    async def delete(self, entity: T) -> None:
        """Xóa entity khỏi database (hard delete)."""
        await self.db.delete(entity)
        await self.db.flush()

    async def soft_delete(
        self,
        entity: T,
        *,
        field_name: str = "is_deleted",
    ) -> T:
        """
        Soft delete — set cờ is_deleted = True.

        Args:
            entity: Entity cần soft delete
            field_name: Tên field dùng làm cờ xóa (mặc định 'is_deleted')
        """
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
