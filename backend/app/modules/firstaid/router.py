from uuid import uuid4, UUID
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import allow_guest, require_admin
from app.modules.users.models import User
from app.modules.audit.dependencies import AuditSvc
from app.modules.firstaid.dependencies import FirstAidSvc
from app.modules.firstaid.schemas.api import (
    CreateGuideRequest,
    FirstAidGuideResponse,
    GuideStatsResponse,
    UpdateGuideRequest,
)
from app.shared.response import SuccessResponse

router = APIRouter(prefix="/first-aid")


@router.get(
    "/guide/{wound_type}/{severity}",
    response_model=SuccessResponse[FirstAidGuideResponse],
    summary="Lấy hướng dẫn sơ cứu cụ thể",
)
async def get_guide(
    wound_type: str,
    severity: str,
    service: FirstAidSvc,
    sub_type: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    guide = await service.get_guide(wound_type, severity, sub_type)
    if not guide:
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
    service: FirstAidSvc,
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    types = await service.get_available_types()
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
    service: FirstAidSvc,
    wound_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = 0,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    # Convert empty strings to None
    wound_type = wound_type.strip() if wound_type and wound_type.strip() else None
    severity = severity.strip() if severity and severity.strip() else None
    search = search.strip() if search and search.strip() else None
    
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
    service: FirstAidSvc,
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
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
    service: FirstAidSvc,
    sub_type: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
    result = await service.check_availability(wound_type, severity, sub_type)
    msg = "Có sẵn" if result["available"] else "Không có sẵn"
    return SuccessResponse(message=msg, data=result)


@router.post(
    "/guides",
    response_model=SuccessResponse[FirstAidGuideResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo hướng dẫn mới (Admin)",
)
async def create_guide(
    request: CreateGuideRequest,
    service: FirstAidSvc,
    audit_service: AuditSvc,
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    guide = await service.create_guide(request, current_user.user_id)
    
    await audit_service.log_event(
        action="create_first_aid_guide",
        user_id=current_user.user_id,
        resource_type="first_aid_guide",
        resource_id=str(guide.id),
        details={"wound_type": guide.wound_type, "severity": guide.severity},
        success=True,
        description=f"Tạo hướng dẫn sơ cứu cho {guide.wound_type} - {guide.severity}"
    )
    
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
    guide_id: UUID,
    service: FirstAidSvc,
    current_user: Optional[User] = Depends(allow_guest),
) -> SuccessResponse:
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
    guide_id: UUID,
    request: UpdateGuideRequest,
    service: FirstAidSvc,
    audit_service: AuditSvc,
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    guide = await service.update_guide(guide_id, request)
    
    await audit_service.log_event(
        action="update_first_aid_guide",
        user_id=current_user.user_id,
        resource_type="first_aid_guide",
        resource_id=str(guide_id),
        details={"wound_type": guide.wound_type, "severity": guide.severity},
        success=True,
        description=f"Cập nhật hướng dẫn sơ cứu: {guide.wound_type} - {guide.severity}"
    )
    
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
    guide_id: UUID,
    service: FirstAidSvc,
    audit_service: AuditSvc,
    hard_delete: bool = False,
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    await service.delete_guide(guide_id, hard_delete)
    
    await audit_service.log_event(
        action="delete_first_aid_guide",
        user_id=current_user.user_id,
        resource_type="first_aid_guide",
        resource_id=str(guide_id),
        details={"hard_delete": hard_delete},
        success=True,
        description=f"Xóa hướng dẫn sơ cứu ID: {guide_id}"
    )
    
    return SuccessResponse(
        message="Xóa thành công",
        data={"guide_id": str(guide_id), "hard_delete": hard_delete},
    )
