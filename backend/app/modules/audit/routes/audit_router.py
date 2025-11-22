from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union

from app.core.database import get_db, get_session
from app.modules.audit.controllers.audit_controller import AuditController
from app.modules.audit.schemas.audit_schemas import (
    AuditLogListResponse,
    AuditStatsResponse,
    AuditLogFilterParams
)
from app.api.v1.deps import require_permission
from app.shared.schemas.response import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/audit")


@router.get(
    "/logs",
    response_model=Union[SuccessResponse[AuditLogListResponse], ErrorResponse],
    summary="Lấy danh sách audit logs",
    description="Lấy danh sách audit logs có lọc và phân trang. Yêu cầu quyền 'read_system_logs'."
)
async def get_audit_logs(
    filters: AuditLogFilterParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(require_permission("read_system_logs"))
) -> Union[SuccessResponse[AuditLogListResponse], ErrorResponse]:
    controller = AuditController(db)
    return await controller.get_audit_logs(filters)


@router.get(
    "/stats",
    response_model=Union[SuccessResponse[AuditStatsResponse], ErrorResponse],
    summary="Lấy thống kê audit",
    description="Lấy thống kê tổng quan về audit logs. Yêu cầu quyền 'read_system_logs'."
)
async def get_audit_stats(
    db: AsyncSession = Depends(get_session),
    current_user = Depends(require_permission("read_system_logs"))
) -> Union[SuccessResponse[AuditStatsResponse], ErrorResponse]:
    controller = AuditController(db)
    return await controller.get_audit_stats()


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Health check",
    description="Kiểm tra trạng thái audit service"
)
async def health_check(
    db: AsyncSession = Depends(get_session)
) -> SuccessResponse[dict]:
    controller = AuditController(db)
    return await controller.health_check()