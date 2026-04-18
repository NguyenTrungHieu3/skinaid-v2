from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field



class RAGDocumentUploadRequest(BaseModel):
    """
    Metadata bổ sung khi admin upload tài liệu RAG.

    File thực tế được gửi qua multipart/form-data (UploadFile),
    schema này chứa metadata tùy chỉnh đi kèm.
    """

    doc_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Metadata tùy chỉnh dạng JSON. "
            "Ví dụ: {\"medical_domain\": \"first_aid\", \"topic\": \"burns\", "
            "\"language\": \"vi\", \"source\": \"WHO\", \"version\": \"2024\"}"
        ),
    )



class RAGDocumentResponse(BaseModel):
    """
    Response schema cho một tài liệu RAG.
    Ánh xạ từ model RagDocument — không expose storage_path vì đó là internal path.
    """

    rag_document_id: UUID = Field(description="UUID định danh tài liệu")
    file_name: str = Field(description="Tên file gốc khi upload")
    file_type: str = Field(description="Extension file (pdf, md, txt, docx, html, csv)")
    status: str = Field(
        description="Trạng thái: pending | indexing | indexed | failed | deleted"
    )
    chunk_count: int = Field(description="Số chunks đã index vào Qdrant")
    error_message: Optional[str] = Field(
        default=None,
        description="Thông báo lỗi nếu status=failed"
    )
    doc_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata tùy chỉnh"
    )
    uploaded_by: Optional[UUID] = Field(
        default=None,
        description="UUID của user đã upload"
    )
    created_at: datetime = Field(description="Thời điểm tạo (UTC)")
    updated_at: datetime = Field(description="Thời điểm cập nhật cuối (UTC)")

    model_config = {"from_attributes": True}


class RAGDocumentListResponse(BaseModel):
    """
    Response schema cho danh sách tài liệu RAG (có phân trang).
    """

    items: List[RAGDocumentResponse] = Field(
        default_factory=list,
        description="Danh sách tài liệu"
    )
    total: int = Field(description="Tổng số tài liệu khớp với filter")
    skip: int = Field(description="Offset đã áp dụng")
    limit: int = Field(description="Limit đã áp dụng")


class RAGDocumentDeleteResponse(BaseModel):
    """
    Response schema khi xóa tài liệu RAG.
    """

    rag_document_id: UUID = Field(description="UUID tài liệu đã xóa")
    file_name: str = Field(description="Tên file đã xóa")
    vectors_deleted: int = Field(
        description="Số Qdrant points đã xóa"
    )
    message: str = Field(
        default="Tài liệu và các vector đã được xóa thành công"
    )


class RAGHealthResponse(BaseModel):
    """
    Response schema cho health check Qdrant collection.
    """

    collection_name: str = Field(description="Tên collection Qdrant")
    status: str = Field(description="Trạng thái collection (green | yellow | red)")
    points_count: int = Field(description="Số points (chunks) đang lưu")
    vectors_count: Optional[int] = Field(
        default=None,
        description="Số vectors trong collection"
    )
    qdrant_connected: bool = Field(description="Qdrant có kết nối được không")
