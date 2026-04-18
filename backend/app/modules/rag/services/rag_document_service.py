from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.rag.exceptions import (
    RAGDocumentNotFoundError,
    RAGIndexingError,
    UnsupportedFileTypeError,
)
from app.modules.rag.models.rag_document import (
    RAG_SUPPORTED_FILE_TYPES,
    RagDocument,
)
from app.modules.rag.repository.rag_document_repository import RAGDocumentRepository
from app.modules.rag.services.chunking_service import chunking_service
from app.modules.rag.services.loader_service import loader_service
from app.modules.rag.services.qdrant_service import ChunkInput, qdrant_service
from app.modules.rag.schemas.rag_document_schemas import RAGDocumentResponse
from app.modules.rag.schemas.rag_schemas import KnowledgeChunk, RAGRetrieveResponse

logger = logging.getLogger(__name__)


class RAGDocumentService:
    def __init__(
        self,
        repository: RAGDocumentRepository,
        db: AsyncSession,
    ) -> None:
        self.repository = repository
        self.db = db

    async def upload_document(
        self,
        file: UploadFile,
        background_tasks: BackgroundTasks,
        uploaded_by: Optional[uuid.UUID] = None,
        doc_metadata: Optional[Dict[str, Any]] = None,
    ) -> RagDocument:
        """
        Accept a file upload from admin, save to disk, create a RagDocument (pending),
        and register a background task for indexing.
        """
        if not file.filename:
            raise UnsupportedFileTypeError(
                message="Invalid filename",
                details={"filename": file.filename},
            )

        safe_filename = Path(file.filename).name
        if not safe_filename or safe_filename in (".", ".."):
            raise UnsupportedFileTypeError(
                message="Invalid filename",
                details={"filename": file.filename},
            )

        file_ext = Path(safe_filename).suffix.lower().lstrip(".")
        if file_ext not in RAG_SUPPORTED_FILE_TYPES:
            raise UnsupportedFileTypeError(
                message=f"File type '.{file_ext}' is not supported",
                details={
                    "file_type": file_ext,
                    "supported": list(RAG_SUPPORTED_FILE_TYPES),
                },
            )

        docs_dir = Path(settings.RAG_DOCS_PATH)
        docs_dir.mkdir(parents=True, exist_ok=True)

        storage_path = str(docs_dir / safe_filename)
        file_bytes = await file.read()
        Path(storage_path).write_bytes(file_bytes)

        logger.info("[RAGDocumentService] Saved file: %s (%d bytes)", storage_path, len(file_bytes))

        doc = RagDocument.create(
            file_name=safe_filename,
            file_type=file_ext,
            storage_path=storage_path,
            uploaded_by=uploaded_by,
            doc_metadata=doc_metadata,
        )

        doc = await self.repository.create(doc)
        
        # Explicit commit to avoid race condition with background task (Read Committed isolation)
        await self.db.commit()

        logger.info(
            "[RAGDocumentService] Created RagDocument id=%s, file='%s', status=pending",
            str(doc.rag_document_id),
            doc.file_name,
        )

        background_tasks.add_task(
            self._index_document_background,
            doc_id=doc.rag_document_id,
            storage_path=storage_path,
        )

        return doc

    async def _index_document_background(
        self,
        doc_id: uuid.UUID,
        storage_path: str,
    ) -> None:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as bg_session:
            repo = RAGDocumentRepository(bg_session)

            doc = await repo.get_by_id(doc_id)
            if not doc:
                logger.error("[RAGIndexing] Document id=%s not found in DB", doc_id)
                return

            doc.mark_indexing()
            await bg_session.flush()
            await bg_session.commit()

            logger.info("[RAGIndexing] Starting index: id=%s, file='%s'", doc_id, doc.file_name)

            try:
                file_path = Path(storage_path)
                text = await loader_service.load(file_path)
                logger.info("[RAGIndexing] Loaded %d chars from '%s'", len(text), doc.file_name)

                chunks = await chunking_service.chunk(text)
                logger.info("[RAGIndexing] Created %d chunks", len(chunks))

                if not chunks:
                    raise RAGIndexingError(
                        message="No chunks could be created from the document",
                        details={"file_name": doc.file_name},
                    )

                chunk_inputs = [
                    ChunkInput(
                        document_id=str(doc_id),
                        chunk_index=chunk.chunk_index,
                        file_type=doc.file_type,
                        content=chunk.content,
                        context=chunk.context,
                    )
                    for chunk in chunks
                ]

                indexed_count = await qdrant_service.upsert_documents(chunk_inputs)
                logger.info("[RAGIndexing] Upserted %d chunks to Qdrant", indexed_count)

                doc.mark_indexed(chunk_count=indexed_count)
                await bg_session.flush()
                await bg_session.commit()

                logger.info(
                    "[RAGIndexing] Completed: id=%s, file='%s', chunks=%d",
                    doc_id,
                    doc.file_name,
                    indexed_count,
                )

            except Exception as exc:
                error_msg = str(exc)[:2000]
                doc.mark_failed(error=error_msg)
                try:
                    await bg_session.flush()
                    await bg_session.commit()
                except Exception as commit_err:
                    logger.error(
                        "[RAGIndexing] Could not commit mark_failed: %s", str(commit_err)
                    )

                logger.error(
                    "[RAGIndexing] Failed: id=%s, file='%s', error=%s",
                    doc_id,
                    doc.file_name,
                    error_msg,
                )

    async def delete_document(self, doc_id: uuid.UUID) -> Tuple[str, int]:
        """
        Delete a RAG document: remove Qdrant vectors first, then delete the DB record.

        Order matters:
            1. Delete Qdrant points (can be retried if step 2 fails)
            2. Hard-delete DB record

        If Qdrant deletion succeeds but DB deletion fails, the caller can retry delete.
        """
        doc = await self.repository.get_by_id(doc_id)
        if not doc or doc.status == "deleted":
            raise RAGDocumentNotFoundError(
                message=f"RAG document not found: {doc_id}",
                details={"rag_document_id": str(doc_id)},
            )

        file_name = doc.file_name

        vectors_deleted = await qdrant_service.delete_by_document_id(str(doc_id))
        logger.info(
            "[RAGDocumentService] Deleted %d Qdrant points for doc_id=%s",
            vectors_deleted,
            doc_id,
        )

        await self.repository.delete(doc)

        logger.info(
            "[RAGDocumentService] Deleted RagDocument id=%s, file='%s'",
            doc_id,
            file_name,
        )

        return file_name, vectors_deleted

    async def get_document(self, doc_id: uuid.UUID) -> RagDocument:
        """Get a single RAG document by ID."""
        doc = await self.repository.get_by_id(doc_id)
        if not doc or doc.status == "deleted":
            raise RAGDocumentNotFoundError(
                message=f"RAG document not found: {doc_id}",
                details={"rag_document_id": str(doc_id)},
            )
        return doc

    async def list_documents(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Tuple[Sequence[RagDocument], int]:
        """List RAG documents with pagination and filtering."""
        limit = min(limit, 100)
        return await self.repository.get_all(
            skip=skip,
            limit=limit,
            status=status,
            file_type=file_type,
        )

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RAGRetrieveResponse:
        """Hybrid search on Qdrant to retrieve relevant chunks."""
        import time
        start_ms = int(time.time() * 1000)

        top_k = max(1, min(top_k, 20))

        retrieved = await qdrant_service.hybrid_search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        elapsed_ms = int(time.time() * 1000) - start_ms

        chunks = [
            KnowledgeChunk(
                chunk_id=r.point_id,
                content=str(r.metadata.get("content", "") or r.content),
                source=r.document_id,
                relevance_score=r.score,
                metadata={
                    "document_id": r.document_id,
                    "chunk_index": r.chunk_index,
                    "file_type": r.file_type,
                    "context": r.context,
                },
            )
            for r in retrieved
        ]

        return RAGRetrieveResponse(
            chunks=chunks,
            source="knowledge_base",
            total_found=len(chunks),
            query_time_ms=elapsed_ms,
        )
