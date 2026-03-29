from __future__ import annotations

import uuid
from typing import Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rag.models.rag_document import RagDocument
from app.shared.base_repository import BaseRepository


class RAGDocumentRepository(BaseRepository[RagDocument]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=RagDocument, db=db)

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Tuple[Sequence[RagDocument], int]:
        """Lấy danh sách tài liệu có phân trang và lọc theo status/file_type. Mặc định ẩn deleted."""
        filters = []
        if status is not None:
            filters.append(RagDocument.status == status)
        else:
            filters.append(RagDocument.status != "deleted")

        if file_type is not None:
            filters.append(RagDocument.file_type == file_type.lower())

        count_stmt = select(func.count()).select_from(RagDocument).where(*filters)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        data_stmt = (
            select(RagDocument)
            .where(*filters)
            .order_by(RagDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.db.execute(data_stmt)
        items = data_result.scalars().all()

        return items, total

    async def get_by_status(self, status: str) -> Sequence[RagDocument]:
        """Lấy tất cả tài liệu theo trạng thái cụ thể, sắp xếp theo created_at DESC."""
        stmt = (
            select(RagDocument)
            .where(RagDocument.status == status)
            .order_by(RagDocument.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_uploader(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[RagDocument], int]:
        """Lấy tài liệu do một user cụ thể upload."""
        filters = [
            RagDocument.uploaded_by == user_id,
            RagDocument.status != "deleted",
        ]

        count_stmt = select(func.count()).select_from(RagDocument).where(*filters)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        data_stmt = (
            select(RagDocument)
            .where(*filters)
            .order_by(RagDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.db.execute(data_stmt)
        items = data_result.scalars().all()

        return items, total
