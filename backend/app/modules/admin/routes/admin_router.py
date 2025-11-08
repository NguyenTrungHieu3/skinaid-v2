from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.schemas.response import SuccessResponse
from app.modules.admin.controllers.admin_controller import AdminController
from app.modules.admin.schemas.admin_schemas import (
    DashboardOverviewResponse,
    WoundTypeDistributionResponse,
    WeeklyActivityResponse,
    SystemLogsResponse,
    SeverityStatsResponse
)
from app.api.v1.deps import get_db, require_admin
from app.modules.auth.models.user import User
from app.core.database import get_session

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


async def get_admin_controller(db: AsyncSession = Depends(get_db)) -> AdminController:
    """Dependency to get admin controller instance"""
    return AdminController(db)


@router.get(
    "/dashboard/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Get Dashboard Overview",
    description="Get overview statistics for admin dashboard (4 main cards)"
)
async def get_dashboard_overview(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get dashboard overview statistics including:
    - Total users and active today
    - Total images and analyzed count
    - Model accuracy metrics
    - Session statistics
    
    **Requires admin role**
    """
    return await controller.get_dashboard_overview()


@router.get(
    "/wound-types/distribution",
    response_model=SuccessResponse[WoundTypeDistributionResponse],
    summary="Get Wound Type Distribution",
    description="Get distribution of wound types for pie chart visualization"
)
async def get_wound_type_distribution(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get wound type distribution data for pie chart:
    - Wound type names (Abrasion, Burn, Bruise, etc.)
    - Count for each type
    - Display colors
    
    **Requires admin role**
    """
    return await controller.get_wound_type_distribution()


@router.get(
    "/activity/weekly",
    response_model=SuccessResponse[WeeklyActivityResponse],
    summary="Get Weekly Activity",
    description="Get weekly activity statistics for bar chart (last 7 days)"
)
async def get_weekly_activity(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get weekly activity statistics for bar chart:
    - Daily upload counts
    - Daily analysis counts
    - Last 7 days of data
    
    **Requires admin role**
    """
    return await controller.get_weekly_activity()


@router.get(
    "/severity/stats",
    response_model=SuccessResponse[SeverityStatsResponse],
    summary="Get Severity Level Statistics",
    description="Get distribution of wound severity levels (Mild, Moderate, Severe)"
)
async def get_severity_stats(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get severity level statistics for bar chart:
    - Mild wound count
    - Moderate wound count
    - Severe wound count
    - Total detections
    
    **Requires admin role**
    """
    return await controller.get_severity_stats()


@router.get(
    "/logs/recent",
    response_model=SuccessResponse[SystemLogsResponse],
    summary="Get Recent System Logs",
    description="Get recent system logs and alerts for monitoring"
)
async def get_system_logs(
    limit: int = Query(10, ge=1, le=50, description="Number of logs to retrieve"),
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get recent system logs and alerts:
    - Error logs
    - Warning messages
    - Info notifications
    - Success events
    
    **Requires admin role**
    """
    return await controller.get_system_logs(limit=limit)


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Admin Service Health Check",
    description="Check if admin service is healthy"
)
async def admin_health_check():
    """Health check endpoint for admin service"""
    return SuccessResponse(
        message="Admin service is healthy",
        data={
            "status": "healthy",
            "service": "admin_dashboard",
            "version": "1.0.0"
        }
    )
