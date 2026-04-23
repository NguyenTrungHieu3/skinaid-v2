"""Repository cho rag_documents — extend BaseRepository."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rag.models.rag_document import RagDocument
from app.shared.base_repository import BaseRepository


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RagDocumentRepository(BaseRepository[RagDocument]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(RagDocument, db)

    async def list_documents(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> tuple[list[RagDocument], int]:
        filters = []
        if status:
            filters.append(RagDocument.status == status)

        stmt = (
            select(RagDocument)
            .where(*filters)
            .order_by(RagDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = await self.get_many_by_stmt(stmt)
        total = await self.count(*filters)
        return list(items), total

    async def update_status(
        self,
        doc: RagDocument,
        status: str,
        *,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None,
        indexed_at: Optional[datetime] = None,
    ) -> RagDocument:
        data: dict = {"status": status, "updated_at": _now()}
        if chunk_count is not None:
            data["chunk_count"] = chunk_count
        if error_message is not None:
            data["error_message"] = error_message[:2000]
        if indexed_at is not None:
            data["indexed_at"] = indexed_at
        return await self.update(doc, data)

    async def get(self, doc_id: UUID) -> Optional[RagDocument]:
        return await self.get_by_id(doc_id)
