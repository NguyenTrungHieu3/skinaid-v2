from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import AsyncSessionLocal
from app.modules.rag.exceptions import IndexingError
from app.modules.rag.repository.rag_document_repository import RagDocumentRepository
from app.modules.rag.services.chunking_service import ChunkingService
from app.modules.rag.services.loader_service import LoaderService
from app.modules.rag.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class IndexingService:
    def __init__(
        self,
        loader: LoaderService,
        chunking: ChunkingService,
        qdrant: QdrantService,
    ) -> None:
        self._loader = loader
        self._chunking = chunking
        self._qdrant = qdrant

    async def index_document(self, document_id: UUID) -> None:
        async with AsyncSessionLocal() as session:
            repo = RagDocumentRepository(session)
            doc = await repo.get_by_id(document_id)
            if doc is None:
                return

            await repo.update_status(doc, "indexing")
            await session.commit()

            try:
                text = self._loader.load(doc.storage_path, doc.file_type)
                chunks = self._chunking.semantic_split(text)
                if not chunks:
                    raise IndexingError("Semantic chunking trả về 0 chunks")

                contextualized = await self._chunking.add_context(text, chunks)
                await self._qdrant.delete_by_document_id(document_id)
                count = await self._qdrant.upsert_chunks(
                    document_id=document_id,
                    embed_texts=contextualized,
                    original_chunks=chunks,
                    doc_metadata=doc.doc_metadata,
                )

                await repo.update_status(
                    doc, "indexed", chunk_count=count, indexed_at=_now(), error_message=None,
                )
                await session.commit()
                logger.info("[RAG] indexed doc=%s chunks=%d", document_id, count)
            except Exception as exc:
                logger.error("[RAG] indexing failed doc=%s: %s", document_id, exc)
                try:
                    await repo.update_status(doc, "failed", error_message=str(exc))
                    await session.commit()
                except Exception:
                    pass
