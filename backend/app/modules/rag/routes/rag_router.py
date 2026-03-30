from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status

from app.core.dependencies.access_control import require_admin, require_auth
from app.modules.users.models.user import User
from app.modules.rag.dependencies import get_rag_document_service
from app.modules.rag.services.rag_document_service import RAGDocumentService
from app.modules.rag.services.qdrant_service import qdrant_service
from app.modules.rag.schemas.rag_document_schemas import (
    RAGDocumentDeleteResponse,
    RAGDocumentListResponse,
    RAGDocumentResponse,
    RAGHealthResponse,
)
from app.modules.rag.schemas.rag_schemas import RAGRetrieveRequest, RAGRetrieveResponse
from app.shared.response import SuccessResponse

router = APIRouter(tags=["RAG - Knowledge Retrieval"])

@router.post(
    "/documents",
    response_model=SuccessResponse[RAGDocumentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload tài liệu RAG (Admin)",
    description=(
        "Admin upload file tài liệu vào knowledge base. "
        "File được lưu vào disk và indexing chạy bất đồng bộ (background task). "
        "Response trả về ngay với status=pending. "
        "Định dạng hỗ trợ: pdf, md, txt, docx, html, csv."
    ),
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="File tài liệu cần index"),
    doc_metadata: Optional[str] = Query(
        None,
        description='Metadata JSON (vd: \'{"topic": "burns", "source": "WHO"}\')',
    ),
    service: RAGDocumentService = Depends(get_rag_document_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    parsed_metadata = None
    if doc_metadata:
        try:
            parsed_metadata = json.loads(doc_metadata)
        except json.JSONDecodeError:
            parsed_metadata = {"raw": doc_metadata}

    doc = await service.upload_document(
        file=file,
        background_tasks=background_tasks,
        uploaded_by=current_user.user_id,
        doc_metadata=parsed_metadata,
    )

    return SuccessResponse(
        message=f"Upload thành công. Đang indexing '{doc.file_name}' ở nền...",
        data=RAGDocumentResponse.model_validate(doc),
        status_code=status.HTTP_201_CREATED,
    )

@router.get(
    "/documents",
    response_model=SuccessResponse[RAGDocumentListResponse],
    summary="Danh sách tài liệu RAG (Admin)",
    description="Lấy danh sách tài liệu RAG với phân trang và filter theo status/file_type.",
)
async def list_documents(
    skip: int = Query(0, ge=0, description="Offset (bỏ qua N bản ghi đầu)"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Lọc theo trạng thái: pending|indexing|indexed|failed|deleted",
    ),
    file_type: Optional[str] = Query(
        None,
        description="Lọc theo loại file: pdf|md|txt|docx|html|csv",
    ),
    service: RAGDocumentService = Depends(get_rag_document_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    items, total = await service.list_documents(
        skip=skip,
        limit=limit,
        status=status_filter,
        file_type=file_type,
    )

    return SuccessResponse(
        message=f"Tìm thấy {total} tài liệu RAG",
        data=RAGDocumentListResponse(
            items=[RAGDocumentResponse.model_validate(doc) for doc in items],
            total=total,
            skip=skip,
            limit=limit,
        ),
    )

@router.get(
    "/documents/{doc_id}",
    response_model=SuccessResponse[RAGDocumentResponse],
    summary="Chi tiết tài liệu RAG (Admin)",
)
async def get_document(
    doc_id: uuid.UUID,
    service: RAGDocumentService = Depends(get_rag_document_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    doc = await service.get_document(doc_id)
    return SuccessResponse(
        message="Lấy thông tin tài liệu thành công",
        data=RAGDocumentResponse.model_validate(doc),
    )

@router.delete(
    "/documents/{doc_id}",
    response_model=SuccessResponse[RAGDocumentDeleteResponse],
    summary="Xóa tài liệu RAG (Admin)",
    description=(
        "Xóa tài liệu RAG. "
        "Thứ tự: (1) xóa Qdrant vectors → (2) xóa DB record. "
        "Đảm bảo không có orphan vectors trong Qdrant."
    ),
)
async def delete_document(
    doc_id: uuid.UUID,
    service: RAGDocumentService = Depends(get_rag_document_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    file_name, vectors_deleted = await service.delete_document(doc_id)

    return SuccessResponse(
        message=f"Đã xóa tài liệu '{file_name}' và {vectors_deleted} vectors",
        data=RAGDocumentDeleteResponse(
            rag_document_id=doc_id,
            file_name=file_name,
            vectors_deleted=vectors_deleted,
        ),
    )

@router.post(
    "/retrieve",
    response_model=SuccessResponse[RAGRetrieveResponse],
    summary="Tìm kiếm RAG knowledge",
    description=(
        "Hybrid search (dense + BM25 sparse) trên Qdrant knowledge base. "
        "Trả về các chunks liên quan nhất theo relevance_score. "
        "Dùng trong B5 pipeline sau khi user trả lời questionnaire."
    ),
)
async def retrieve(
    request: RAGRetrieveRequest,
    service: RAGDocumentService = Depends(get_rag_document_service),
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    result = await service.search(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters,
    )

    return SuccessResponse(
        message="Truy xuất tri thức thành công",
        data=result,
    )

@router.get(
    "/health",
    response_model=SuccessResponse[RAGHealthResponse],
    summary="Health check Qdrant collection (Admin)",
    description="Kiểm tra trạng thái kết nối Qdrant và thông tin collection.",
)
async def health_check(
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        info = await qdrant_service.get_collection_info()
        return SuccessResponse(
            message="Qdrant đang hoạt động bình thường",
            data=RAGHealthResponse(
                collection_name=info.get("collection_name", ""),
                status=info.get("status", "unknown"),
                points_count=info.get("points_count", 0),
                vectors_count=info.get("vectors_count"),
                qdrant_connected=True,
            ),
        )
    except Exception as exc:
        return SuccessResponse(
            message=f"Qdrant không khả dụng: {str(exc)}",
            data=RAGHealthResponse(
                collection_name="",
                status="red",
                points_count=0,
                qdrant_connected=False,
            ),
            status_code=503,
        )
