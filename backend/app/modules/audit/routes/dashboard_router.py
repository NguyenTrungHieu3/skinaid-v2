"""
Dashboard Router - Statistics and Analytics for Admin

Endpoints for dashboard statistics (requires admin role).
Moved from admin module - admin is a role, not a module.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.response import SuccessResponse
from app.modules.audit.services.statistics_service import StatisticsService
from app.modules.audit.schemas.dashboard_schemas import (
    DashboardOverviewResponse,
    WoundTypeDistributionResponse,
    WeeklyActivityResponse,
    SystemLogsResponse,
    SeverityStatsResponse
)
from app.core.dependencies import get_db, require_admin
from app.modules.auth.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])


def get_statistics_service(db: AsyncSession = Depends(get_db)) -> StatisticsService:
    """Dependency to get StatisticsService instance"""
    return StatisticsService(db)


@router.get(
    "/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Get Dashboard Overview",
    description="Get overview statistics for admin dashboard (4 main cards)"
)
async def get_dashboard_overview(
    period: str = Query("month", enum=["day", "week", "month", "year", "all"], description="Statistics period"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Get dashboard overview statistics including:
    - Total users and active users today
    - Total images and analyzed count
    - Model accuracy metrics
    - Session statistics

    **Requires admin role**
    """
    data = await service.get_dashboard_overview(period=period)
    response = DashboardOverviewResponse(**data)
    return SuccessResponse(
        message="Dashboard overview retrieved successfully",
        data=response
    )


@router.get(
    "/wound-types/distribution",
    response_model=SuccessResponse[WoundTypeDistributionResponse],
    summary="Get Wound Type Distribution",
    description="Get wound type distribution for pie chart"
)
async def get_wound_type_distribution(
    period: str = Query("month", enum=["day", "week", "month", "year", "all"], description="Statistics period"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Get wound type distribution data for pie chart:
    - Wound type name (Abrasion, Burn, Bruise, etc.)
    - Count for each type
    - Display color

    **Requires admin role**
    """
    data = await service.get_wound_type_distribution(period=period)
    response = WoundTypeDistributionResponse(**data)
    return SuccessResponse(
        message="Wound type distribution retrieved successfully",
        data=response
    )


@router.get(
    "/activity/weekly",
    response_model=SuccessResponse[WeeklyActivityResponse],
    summary="Get Weekly Activity",
    description="Get weekly activity statistics for bar chart (last 7 days)"
)
async def get_weekly_activity(
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Get weekly activity statistics for bar chart:
    - Daily uploads count
    - Daily analyses count
    - Last 7 days data

    **Requires admin role**
    """
    data = await service.get_weekly_activity()
    response = WeeklyActivityResponse(**data)
    return SuccessResponse(
        message="Weekly activity retrieved successfully",
        data=response
    )


@router.get(
    "/severity/stats",
    response_model=SuccessResponse[SeverityStatsResponse],
    summary="Get Severity Statistics",
    description="Get wound severity distribution (Mild, Moderate, Severe)"
)
async def get_severity_stats(
    period: str = Query("month", enum=["day", "week", "month", "year", "all"], description="Statistics period"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Get severity statistics for bar chart:
    - Mild wound count
    - Moderate wound count
    - Severe wound count
    - Total detections

    **Requires admin role**
    """
    data = await service.get_severity_stats(period=period)
    response = SeverityStatsResponse(**data)
    return SuccessResponse(
        message="Severity statistics retrieved successfully",
        data=response
    )


@router.get(
    "/logs/recent",
    response_model=SuccessResponse[SystemLogsResponse],
    summary="Get Recent System Logs",
    description="Get recent system logs and warnings for monitoring"
)
async def get_system_logs(
    limit: int = Query(10, ge=1, le=50, description="Number of logs to retrieve"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Get recent system logs and warnings:
    - Error logs
    - Warning messages
    - Info messages
    - Success events

    **Requires admin role**
    """
    data = await service.get_system_logs(limit=limit)
    response = SystemLogsResponse(**data)
    return SuccessResponse(
        message="System logs retrieved successfully",
        data=response
    )


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Dashboard Service Health Check",
    description="Check if dashboard service is working properly",
)
async def dashboard_health_check():
    """Health check endpoint for dashboard service"""
    return SuccessResponse(
        message="Dashboard service is healthy",
        data={
            "status": "healthy",
            "service": "dashboard_analytics",
            "version": "1.0.0",
        },
    )
