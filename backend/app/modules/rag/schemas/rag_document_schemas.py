"""Request/Response schemas cho RAG document endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    """Representation của 1 rag_document."""

    model_config = ConfigDict(from_attributes=True)

    rag_document_id: UUID
    file_name: str
    file_type: str
    file_size_bytes: Optional[int] = None
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    indexed_at: Optional[datetime] = None
    doc_metadata: Optional[dict[str, Any]] = None
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[DocumentResponse]


class DocumentDeleteResponse(BaseModel):
    rag_document_id: UUID
    file_name: str = ""
    deleted_points: int = Field(0, description="Số Qdrant points đã xóa")
    message: str = "Document deleted"


class HealthResponse(BaseModel):
    status: str
    qdrant_ok: bool
    collection: str
    points_count: Optional[int] = None
    detail: Optional[str] = None
