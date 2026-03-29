from __future__ import annotations

from typing import Any

from app.shared.exceptions.base import (
    AppException,
    BadRequestError,
    InternalError,
    NotFoundError,
)


class RAGException(AppException):
    """Base exception cho toàn bộ module RAG."""

    status_code: int = 500
    error_code: str = "RAG_ERROR"

    def __init__(
        self,
        message: str = "Đã xảy ra lỗi RAG",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class QdrantCollectionError(RAGException):
    """Lỗi khi thao tác với Qdrant collection (HTTP 503)."""

    status_code: int = 503
    error_code: str = "QDRANT_COLLECTION_ERROR"

    def __init__(
        self,
        message: str = "Lỗi kết nối hoặc thao tác với Qdrant collection",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class QdrantSearchError(RAGException):
    """Lỗi khi thực hiện hybrid search trên Qdrant (HTTP 503)."""

    status_code: int = 503
    error_code: str = "QDRANT_SEARCH_ERROR"

    def __init__(
        self,
        message: str = "Tìm kiếm vector thất bại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class QdrantUpsertError(RAGException):
    """Lỗi khi upsert document chunks vào Qdrant (HTTP 503)."""

    status_code: int = 503
    error_code: str = "QDRANT_UPSERT_ERROR"

    def __init__(
        self,
        message: str = "Không thể upsert tài liệu vào Qdrant",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class QdrantDeleteError(RAGException):
    """Lỗi khi xóa vector points khỏi Qdrant (HTTP 503)."""

    status_code: int = 503
    error_code: str = "QDRANT_DELETE_ERROR"

    def __init__(
        self,
        message: str = "Không thể xóa vector points khỏi Qdrant",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class RAGDocumentNotFoundError(NotFoundError):
    """Tài liệu RAG không tồn tại trong database (HTTP 404)."""

    error_code: str = "RAG_DOCUMENT_NOT_FOUND"

    def __init__(
        self,
        message: str = "Tài liệu RAG không tìm thấy",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class UnsupportedFileTypeError(BadRequestError):
    """Định dạng file không được hỗ trợ bởi RAG loader (HTTP 400)."""

    error_code: str = "RAG_UNSUPPORTED_FILE_TYPE"

    def __init__(
        self,
        message: str = "Định dạng file không được hỗ trợ cho RAG indexing",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class RAGIndexingError(InternalError):
    """Lỗi trong quá trình index pipeline (HTTP 500)."""

    error_code: str = "RAG_INDEXING_ERROR"

    def __init__(
        self,
        message: str = "Lỗi trong quá trình index tài liệu RAG",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class RAGServiceNotInitializedError(RAGException):
    """QdrantService chưa được khởi tạo trước khi sử dụng (HTTP 500)."""

    status_code: int = 500
    error_code: str = "RAG_SERVICE_NOT_INITIALIZED"

    def __init__(
        self,
        message: str = "QdrantService chưa được khởi tạo. Kiểm tra lifespan startup.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
