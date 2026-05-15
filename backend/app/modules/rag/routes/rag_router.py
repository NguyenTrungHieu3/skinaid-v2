"""RAG admin endpoints — exceptions handled by app-level handlers."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)

from app.core.dependencies import require_admin
from app.modules.rag.dependencies import (
    get_qdrant_service,
    get_rag_document_service,
)
from app.modules.rag.schemas.rag_document_schemas import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    HealthResponse,
)
from app.modules.rag.services.qdrant_service import QdrantService
from app.modules.rag.services.rag_document_service import RagDocumentService
from app.modules.users.models import User
from app.modules.audit.dependencies import get_audit_service
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/rag", tags=["RAG - Knowledge Retrieval"])


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_metadata: Optional[str] = Form(
        default=None,
        description='JSON string optional (e.g. {"wound_type": "burn"})',
    ),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(require_admin),
    service: RagDocumentService = Depends(get_rag_document_service),
) -> DocumentResponse:
    doc = await service.upload(
        file=file,
        uploaded_by=current_user.user_id,
        doc_metadata_raw=doc_metadata,
        background_tasks=background_tasks,
    )
    
    await audit_service.log_event(
        action="upload_rag_document",
        user_id=current_user.user_id,
        resource_type="rag_document",
        resource_id=str(doc.rag_document_id),
        details={"file_name": doc.file_name, "file_type": doc.file_type},
        success=True,
        description=f"Tải lên tài liệu cơ sở tri thức: {doc.file_name}"
    )
    
    return DocumentResponse.model_validate(doc)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    file_type_filter: Optional[str] = Query(None, alias="file_type"),
    _admin: User = Depends(require_admin),
    service: RagDocumentService = Depends(get_rag_document_service),
) -> DocumentListResponse:
    items, total = await service.list_documents(
        skip=skip,
        limit=limit,
        status=status_filter,
        file_type=file_type_filter,
    )
    return DocumentListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[DocumentResponse.model_validate(d) for d in items],
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: UUID,
    _admin: User = Depends(require_admin),
    service: RagDocumentService = Depends(get_rag_document_service),
) -> DocumentResponse:
    doc = await service.get_document(doc_id)
    return DocumentResponse.model_validate(doc)


@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: UUID,
    audit_service: AuditService = Depends(get_audit_service),
    _admin: User = Depends(require_admin),
    service: RagDocumentService = Depends(get_rag_document_service),
) -> DocumentDeleteResponse:
    doc = await service.get_document(doc_id)
    file_name = doc.file_name
    deleted = await service.delete_document(doc_id)
    
    await audit_service.log_event(
        action="delete_rag_document",
        user_id=_admin.user_id,
        resource_type="rag_document",
        resource_id=str(doc_id),
        details={"file_name": file_name, "vectors_deleted": deleted},
        success=True,
        description=f"Xóa tài liệu cơ sở tri thức: {file_name}"
    )
    
    return DocumentDeleteResponse(
        rag_document_id=doc_id, file_name=file_name, deleted_points=deleted
    )


@router.get("/health", response_model=HealthResponse)
async def health(
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> HealthResponse:
    ok = await qdrant.ping()
    points = await qdrant.count_points() if ok else None
    return HealthResponse(
        status="ok" if ok else "degraded",
        qdrant_ok=ok,
        collection=qdrant.collection_name,
        points_count=points,
        detail=None if ok else "Qdrant not reachable",
    )
