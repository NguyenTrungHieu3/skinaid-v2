from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.rag.exceptions import (
    DocumentNotFound,
    FileTooLarge,
    UnsupportedFileType,
)
from app.modules.rag.models.rag_document import (
    RAG_SUPPORTED_FILE_TYPES,
    RagDocument,
)
from app.modules.rag.repository.rag_document_repository import RagDocumentRepository
from app.modules.rag.services.indexing_service import IndexingService
from app.modules.rag.services.qdrant_service import QdrantService
from app.shared.services.file_service import FileService

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50MB


class RagDocumentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: RagDocumentRepository,
        indexing: IndexingService,
        qdrant: QdrantService,
    ) -> None:
        self._session = session
        self._repo = repository
        self._indexing = indexing
        self._qdrant = qdrant

    async def upload(
        self,
        *,
        file: UploadFile,
        uploaded_by: Optional[UUID],
        doc_metadata_raw: Optional[str],
        background_tasks: BackgroundTasks,
    ) -> RagDocument:
        file_name = file.filename or "unnamed"
        ext = Path(file_name).suffix.lower().lstrip(".")
        if ext not in RAG_SUPPORTED_FILE_TYPES:
            raise UnsupportedFileType(
                message=f"File type '{ext}' không hỗ trợ",
                details={
                    "file_type": ext,
                    "supported": list(RAG_SUPPORTED_FILE_TYPES),
                },
            )

        content = await file.read()
        size = len(content)
        if size > _MAX_UPLOAD_BYTES:
            raise FileTooLarge(
                message=f"File {size} bytes vượt giới hạn {_MAX_UPLOAD_BYTES}",
                details={"size": size, "max_size": _MAX_UPLOAD_BYTES},
            )

        doc_metadata = self._parse_metadata(doc_metadata_raw)

        storage_dir = Path(settings.RAG_DOCS_PATH)
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_name = f"{uuid4()}.{ext}"
        storage_path = storage_dir / storage_name
        storage_path.write_bytes(content)

        doc = RagDocument.create(
            file_name=file_name,
            file_type=ext,
            storage_path=str(storage_path),
            uploaded_by=uploaded_by,
            doc_metadata=doc_metadata,
        )
        doc.file_size_bytes = size
        doc = await self._repo.create(doc)
        await self._session.commit()
        await self._session.refresh(doc)


        background_tasks.add_task(
            self._indexing.index_document, doc.rag_document_id
        )
        return doc

    async def list_documents(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> tuple[list[RagDocument], int]:
        return await self._repo.list_documents(
            skip=skip, limit=limit, status=status, file_type=file_type
        )

    async def get_document(self, doc_id: UUID) -> RagDocument:
        doc = await self._repo.get(doc_id)
        if doc is None:
            raise DocumentNotFound(
                message=f"Document {doc_id} không tồn tại",
                details={"rag_document_id": str(doc_id)},
            )
        return doc

    async def delete_document(self, doc_id: UUID) -> int:
        doc = await self.get_document(doc_id)
        deleted_points = await self._qdrant.delete_by_document_id(doc_id)
        await FileService.delete_file(doc.storage_path)
        await self._repo.delete(doc)
        await self._session.flush()
        return deleted_points

    def _parse_metadata(self, raw: Optional[str]) -> Optional[dict[str, Any]]:
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

