"""RAG module exceptions — extend shared AppException."""
from __future__ import annotations

from typing import Any

from app.shared.exceptions import (
    BadRequestError,
    InternalError,
    NotFoundError,
    ServiceUnavailableError,
)


class UnsupportedFileType(BadRequestError):
    error_code = "RAG_UNSUPPORTED_FILE_TYPE"

    def __init__(
        self,
        message: str = "File type không được hỗ trợ",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class FileTooLarge(BadRequestError):
    error_code = "RAG_FILE_TOO_LARGE"
    status_code = 413

    def __init__(
        self,
        message: str = "File vượt quá giới hạn kích thước",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class LoaderError(InternalError):
    error_code = "RAG_LOADER_ERROR"

    def __init__(
        self,
        message: str = "Không đọc được file",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class IndexingError(InternalError):
    error_code = "RAG_INDEXING_ERROR"

    def __init__(
        self,
        message: str = "Lỗi khi index tài liệu",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class DocumentNotFound(NotFoundError):
    error_code = "RAG_DOCUMENT_NOT_FOUND"

    def __init__(
        self,
        message: str = "Tài liệu không tồn tại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class QdrantOperationError(ServiceUnavailableError):
    error_code = "RAG_QDRANT_ERROR"

    def __init__(
        self,
        message: str = "Lỗi kết nối Qdrant",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
