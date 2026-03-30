from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

RAG_DOCUMENT_STATUSES = ("pending", "indexing", "indexed", "failed", "deleted")
RAG_SUPPORTED_FILE_TYPES = ("pdf", "md", "txt", "docx", "html", "csv")


def _now() -> datetime:
    """Trả về timestamp UTC hiện tại (naive datetime)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RagDocument(SQLModel, table=True):
    """Metadata của một tài liệu RAG được index vào Qdrant."""

    __tablename__ = "rag_documents"

    rag_document_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="UUID định danh tài liệu — cũng là document_id trong Qdrant payload",
    )

    file_name: str = Field(
        nullable=False,
        max_length=500,
        index=True,
        description="Tên file gốc khi upload",
    )

    file_type: str = Field(
        nullable=False,
        max_length=20,
        index=True,
        description="Extension không có dấu chấm (pdf, md, docx, txt...)",
    )

    storage_path: str = Field(
        nullable=False,
        max_length=1000,
        description="Đường dẫn file đã lưu trên disk hoặc object storage",
    )

    status: str = Field(
        default="pending",
        nullable=False,
        index=True,
        description="Trạng thái indexing: pending | indexing | indexed | failed | deleted",
    )

    chunk_count: int = Field(
        default=0,
        nullable=False,
        description="Số chunks đã được index vào Qdrant",
    )

    error_message: Optional[str] = Field(
        default=None,
        nullable=True,
        max_length=2000,
        description="Thông báo lỗi nếu status='failed'",
    )

    doc_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column("doc_metadata", JSONB, nullable=True),
        description="Metadata tùy chỉnh dạng JSONB",
    )

    uploaded_by: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        nullable=True,
        description="UUID của admin đã upload tài liệu",
    )

    created_at: datetime = Field(
        default_factory=_now,
        nullable=False,
        description="Thời điểm tạo record (UTC)",
    )

    updated_at: datetime = Field(
        default_factory=_now,
        nullable=False,
        description="Thời điểm cập nhật cuối cùng (UTC)",
    )

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
        """Tạo RagDocument mới với status='pending'. Validates file_type."""
        file_type_lower = file_type.lower().lstrip(".")
        if file_type_lower not in RAG_SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"File type '{file_type}' không được hỗ trợ. "
                f"Chấp nhận: {', '.join(RAG_SUPPORTED_FILE_TYPES)}"
            )

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
        """Chuyển status sang 'indexing'."""
        self.status = "indexing"
        self.updated_at = _now()

    def mark_indexed(self, chunk_count: int) -> None:
        """Chuyển status sang 'indexed' và lưu số chunks."""
        self.status = "indexed"
        self.chunk_count = chunk_count
        self.error_message = None
        self.updated_at = _now()

    def mark_failed(self, error: str) -> None:
        """Chuyển status sang 'failed' và lưu thông báo lỗi."""
        self.status = "failed"
        self.error_message = error[:2000]
        self.updated_at = _now()

    def is_searchable(self) -> bool:
        """True nếu tài liệu đã được index và có thể search."""
        return self.status == "indexed" and self.chunk_count > 0

    def __repr__(self) -> str:
        return (
            f"<RagDocument(id={str(self.rag_document_id)[:8]}..., "
            f"file='{self.file_name}', type='{self.file_type}', "
            f"status='{self.status}', chunks={self.chunk_count})>"
        )
