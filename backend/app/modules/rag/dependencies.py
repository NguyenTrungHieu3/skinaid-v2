from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.rag.repository.rag_document_repository import RagDocumentRepository
from app.modules.rag.services.chunking_service import ChunkingService
from app.modules.rag.services.indexing_service import IndexingService
from app.modules.rag.services.loader_service import LoaderService
from app.modules.rag.services.qdrant_service import QdrantService, qdrant_service
from app.modules.rag.services.rag_document_service import RagDocumentService


@lru_cache(maxsize=1)
def _loader_singleton() -> LoaderService:
    return LoaderService()


@lru_cache(maxsize=1)
def _chunking_singleton() -> ChunkingService:
    return ChunkingService()


@lru_cache(maxsize=1)
def _indexing_singleton() -> IndexingService:
    return IndexingService(
        loader=_loader_singleton(),
        chunking=_chunking_singleton(),
        qdrant=qdrant_service,
    )


def get_qdrant_service() -> QdrantService:
    return qdrant_service


def get_rag_document_repository(
    session: AsyncSession = Depends(get_db),
) -> RagDocumentRepository:
    return RagDocumentRepository(session)


def get_rag_document_service(
    session: AsyncSession = Depends(get_db),
    repo: RagDocumentRepository = Depends(get_rag_document_repository),
) -> RagDocumentService:
    return RagDocumentService(
        session=session,
        repository=repo,
        indexing=_indexing_singleton(),
        qdrant=qdrant_service,
    )
