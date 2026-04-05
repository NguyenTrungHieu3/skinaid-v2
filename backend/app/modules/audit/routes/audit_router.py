"""
Audit Logs Router - Full audit log access for Admin.

Provides paginated, filterable access to all system audit logs.
Distinct from dashboard_router which only provides a quick summary.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.shared.response import SuccessResponse
from app.modules.audit.schemas.api import AuditLogFilterParams, AuditLogListResponse
from app.modules.audit.dependencies import AuditSvc
from app.core.dependencies import require_admin
from app.modules.users.models import User

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get(
    "/logs",
    response_model=SuccessResponse[AuditLogListResponse],
    summary="Get Audit Logs",
    description="Get paginated, filterable audit logs for admin monitoring."
)
async def get_audit_logs(
    service: AuditSvc,
    current_user: User = Depends(require_admin),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    is_guest: Optional[bool] = Query(None, description="Filter guest sessions"),
    search: Optional[str] = Query(None, description="Search in action, description, user name, email"),
    role_name: Optional[str] = Query(None, description="Filter by user role"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    log_type: Optional[str] = Query(None, description="Filter by log type: admin_action / user_activity / system_error"),
    level: Optional[str] = Query(None, description="Filter by level: info / warning / error"),
):
    """
    Get all audit logs with full filtering and pagination.

    Supports:
    - Filter by log_type (admin_action / user_activity / system_error)
    - Filter by level (info / warning / error)
    - Filter by success/error status
    - Filter by user role
    - Filter by date range
    - Search by action, description, username, email
    - Pagination (default 20 per page)

    **Requires admin role**
    """
    # Strip timezone info to match database naive datetime columns
    # Database stores timestamps as TIMESTAMP WITHOUT TIME ZONE
    safe_start = start_date.replace(tzinfo=None) if start_date and start_date.tzinfo else start_date
    safe_end = end_date.replace(tzinfo=None) if end_date and end_date.tzinfo else end_date

    filters = AuditLogFilterParams(
        page=page,
        limit=limit,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        success=success,
        is_guest=is_guest,
        search=search,
        role_name=role_name,
        start_date=safe_start,
        end_date=safe_end,
        log_type=log_type,
        level=level,
    )

    logs, total_count = await service.get_audit_logs(filters)
    total_pages = max(1, (total_count + limit - 1) // limit)

    response = AuditLogListResponse(
        logs=logs,
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_more=page < total_pages,
    )

    return SuccessResponse(
        message="Audit logs retrieved successfully",
        data=response,
    )
