import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import allow_guest, require_admin
from app.modules.auth.models.user import User
from app.modules.firstaid.dependencies import get_firstaid_service
from app.modules.firstaid.schemas.api import (
    CreateGuideRequest,
    FirstAidGuideResponse,
    GuideStatsResponse,
    GuideValidationResponse,
    UpdateGuideRequest,
)
from app.modules.firstaid.service import FirstAidService
from app.shared.response import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/first-aid", tags=["First Aid"])


# ── Public Endpoints ─────────────────────────────────────────────────────────


@router.get(
    "/guide/{wound_type}/{severity}",
    response_model=SuccessResponse[FirstAidGuideResponse],
    summary="Lấy hướng dẫn sơ cứu cụ thể",
)
async def get_guide(
    wound_type: str,
    severity: str,
    sub_type: Optional[str] = Query(None),
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    """Lấy hướng dẫn sơ cứu theo loại, mức độ, và loại phụ."""
    guide = await service.get_guide(wound_type, severity, sub_type)
    if not guide:
        # Service logic handled fallback, but if returns None -> Not Found
        # But wait, original controller returned 404 with error details.
        # Service currently returns None if not found (repo returns None).
        # We should raise exception in Service or here?
        # Ideally service raises NotFound. I implemented `get_guide_by_id` raising NotFound.
        # `get_guide` currently returns Optional.
        from app.modules.firstaid.exceptions import FirstAidGuideNotFoundError
        raise FirstAidGuideNotFoundError(
            message=f"Không tìm thấy hướng dẫn cho {wound_type}/{severity}"
        )

    return SuccessResponse(
        message="Tìm thấy hướng dẫn sơ cứu",
        data=FirstAidGuideResponse.model_validate(guide),
    )


@router.get(
    "/wound-types",
    response_model=SuccessResponse[List[Dict[str, Any]]],
    summary="Danh sách loại vết thương",
)
async def get_wound_types(
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    """Lấy danh sách các loại vết thương có sẵn."""
    types = await service.get_available_types()
    # Or define a WoundTypeResponse schema? currently List[Dict]
    return SuccessResponse(
        message="Lấy danh sách thành công",
        data=types,
    )


@router.get(
    "/search",
    response_model=SuccessResponse[List[FirstAidGuideResponse]],
    summary="Tìm kiếm hướng dẫn",
)
async def search_guides(
    wound_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = 0,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    """Tìm kiếm với bộ lọc."""
    items, total = await service.search_guides(
        skip=offset,
        limit=limit,
        wound_type=wound_type,
        severity=severity,
        is_active=is_active,
        search=search,
    )
    return SuccessResponse(
        message=f"Tìm thấy {len(items)} hướng dẫn",
        data=[FirstAidGuideResponse.model_validate(i) for i in items],
        extra={"total": total},
    )


@router.get(
    "/statistics",
    response_model=SuccessResponse[GuideStatsResponse],
    summary="Thống kê dữ liệu",
)
async def get_statistics(
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    """Thống kê tổng quan."""
    stats = await service.get_stats()
    return SuccessResponse(
        message="Lấy thống kê thành công",
        data=stats,
    )


@router.get(
    "/validate/{wound_type}/{severity}",
    response_model=SuccessResponse[Dict[str, Any]],
    summary="Validate availability",
)
async def validate_availability(
    wound_type: str,
    severity: str,
    sub_type: Optional[str] = Query(None),
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    """Kiểm tra hướng dẫn có sẵn không."""
    result = await service.check_availability(wound_type, severity, sub_type)
    msg = "Có sẵn" if result["available"] else "Không có sẵn"
    return SuccessResponse(message=msg, data=result)


# ── Admin Endpoints ──────────────────────────────────────────────────────────


@router.post(
    "/guides",
    response_model=SuccessResponse[FirstAidGuideResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo hướng dẫn mới (Admin)",
)
async def create_guide(
    request: CreateGuideRequest,
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    """Tạo hướng dẫn sơ cứu mới."""
    guide = await service.create_guide(request, current_user.user_id)
    return SuccessResponse(
        message="Tạo hướng dẫn thành công",
        data=FirstAidGuideResponse.model_validate(guide),
    )


@router.get(
    "/guides/{guide_id}",
    response_model=SuccessResponse[FirstAidGuideResponse],
    summary="Lấy chi tiết hướng dẫn",
)
async def get_guide_by_id(
    guide_id: uuid.UUID,
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    """Lấy chi tiết theo ID."""
    guide = await service.get_guide_by_id(guide_id)
    return SuccessResponse(
        message="Lấy hướng dẫn thành công",
        data=FirstAidGuideResponse.model_validate(guide),
    )


@router.put(
    "/guides/{guide_id}",
    response_model=SuccessResponse[FirstAidGuideResponse],
    summary="Cập nhật hướng dẫn (Admin)",
)
async def update_guide(
    guide_id: uuid.UUID,
    request: UpdateGuideRequest,
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    """Cập nhật hướng dẫn."""
    guide = await service.update_guide(guide_id, request)
    return SuccessResponse(
        message="Cập nhật thành công",
        data=FirstAidGuideResponse.model_validate(guide),
    )


@router.delete(
    "/guides/{guide_id}",
    response_model=SuccessResponse[Dict[str, Any]],
    summary="Xóa hướng dẫn (Admin)",
)
async def delete_guide(
    guide_id: uuid.UUID,
    hard_delete: bool = False,
    service: FirstAidService = Depends(get_firstaid_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    """Xóa hướng dẫn (soft hoặc hard)."""
    await service.delete_guide(guide_id, hard_delete)
    return SuccessResponse(
        message="Xóa thành công",
        data={"guide_id": str(guide_id), "hard_delete": hard_delete},
    )
