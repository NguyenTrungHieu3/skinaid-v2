from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.rag.repository.rag_document_repository import RAGDocumentRepository
from app.modules.rag.services.rag_document_service import RAGDocumentService


async def get_rag_repository(
    db: AsyncSession = Depends(get_db),
) -> RAGDocumentRepository:
    """Factory: tạo RAGDocumentRepository với session từ request."""
    return RAGDocumentRepository(db)


async def get_rag_document_service(
    repository: RAGDocumentRepository = Depends(get_rag_repository),
    db: AsyncSession = Depends(get_db),
) -> RAGDocumentService:
    """Factory: tạo RAGDocumentService với repo và session."""
    return RAGDocumentService(repository=repository, db=db)

RagDocumentRepo = Annotated[RAGDocumentRepository, Depends(get_rag_repository)]
RagDocumentSvc = Annotated[RAGDocumentService, Depends(get_rag_document_service)]
