from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

RAG_DOCUMENT_STATUSES = ("pending", "indexing", "indexed", "failed", "deleted")
RAG_SUPPORTED_FILE_TYPES = ("pdf", "md", "txt", "docx", "html", "csv")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RagDocument(SQLModel, table=True):
    __tablename__ = "rag_documents"

    rag_document_id: UUID = Field(default_factory=uuid4, primary_key=True)
    file_name: str = Field(nullable=False, max_length=500, index=True)
    file_type: str = Field(nullable=False, max_length=20, index=True)
    file_size_bytes: Optional[int] = Field(default=None, sa_column=Column("file_size_bytes", BigInteger, nullable=True))
    storage_path: str = Field(nullable=False, max_length=1000)
    status: str = Field(default="pending", nullable=False, max_length=20, index=True)
    chunk_count: int = Field(default=0, nullable=False)
    error_message: Optional[str] = Field(default=None, nullable=True, max_length=2000)
    indexed_at: Optional[datetime] = Field(default=None, nullable=True)
    doc_metadata: Optional[dict[str, Any]] = Field(default=None, sa_column=Column("doc_metadata", JSONB, nullable=True))
    uploaded_by: Optional[UUID] = Field(default=None, foreign_key="users.user_id", nullable=True)
    created_at: datetime = Field(default_factory=_now, nullable=False)
    updated_at: datetime = Field(default_factory=_now, nullable=False)

    __table_args__ = (
        Index("idx_rag_documents_type_status", "file_type", "status"),
        Index("idx_rag_documents_uploaded_by", "uploaded_by", "created_at"),
    )

    @classmethod
    def create(
        cls,
        file_name: str,
        file_type: str,
        storage_path: str,
        uploaded_by: Optional[UUID] = None,
        doc_metadata: Optional[dict[str, Any]] = None,
    ) -> "RagDocument":
        file_type_lower = file_type.lower().lstrip(".")
        if file_type_lower not in RAG_SUPPORTED_FILE_TYPES:
            raise ValueError(f"File type '{file_type}' không hỗ trợ")

        now = _now()
        return cls(
            file_name=file_name,
            file_type=file_type_lower,
            storage_path=storage_path,
            status="pending",
            chunk_count=0,
            uploaded_by=uploaded_by,
            doc_metadata=doc_metadata,
            created_at=now,
            updated_at=now,
        )

    def mark_indexing(self) -> None:
        self.status = "indexing"
        self.updated_at = _now()

    def mark_indexed(self, chunk_count: int) -> None:
        self.status = "indexed"
        self.chunk_count = chunk_count
        self.error_message = None
        self.indexed_at = _now()
        self.updated_at = _now()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error_message = error[:2000]
        self.updated_at = _now()

    def is_searchable(self) -> bool:
        return self.status == "indexed" and self.chunk_count > 0
