from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging
from fastapi import HTTPException, status

from app.shared.schemas.response import SuccessResponse
from app.modules.admin.services.statistics_service import StatisticsService
from app.modules.admin.schemas.admin_schemas import (
    DashboardOverviewResponse,
    WoundTypeDistributionResponse,
    WeeklyActivityResponse,
    SystemLogsResponse,
    SeverityStatsResponse
)

logger = logging.getLogger(__name__)


class AdminController:
    """Controller for admin dashboard endpoints"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stats_service = StatisticsService(db)

    async def get_dashboard_overview(self, period: str = 'month') -> SuccessResponse[DashboardOverviewResponse]:
        """
        Get dashboard overview statistics
        Returns data for all 4 main cards
        """
        try:
            logger.info(f"[ADMIN] Fetching dashboard overview (period: {period})")
            
            overview_data = await self.stats_service.get_dashboard_overview(period=period)
            
            response = DashboardOverviewResponse(**overview_data)

            return SuccessResponse(
                message="Dashboard overview retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get dashboard overview: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve dashboard overview: {str(e)}"
            )

    async def get_wound_type_distribution(self, period: str = 'month') -> SuccessResponse[WoundTypeDistributionResponse]:
        """
        Get wound type distribution for pie chart
        """
        try:
            logger.info(f"[ADMIN] Fetching wound type distribution (period: {period})")
            
            distribution_data = await self.stats_service.get_wound_type_distribution(period=period)
            
            response = WoundTypeDistributionResponse(**distribution_data)

            return SuccessResponse(
                message="Wound type distribution retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get wound type distribution: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve wound type distribution: {str(e)}"
            )

    async def get_weekly_activity(self) -> SuccessResponse[WeeklyActivityResponse]:
        """
        Get weekly activity statistics for bar chart
        """
        try:
            logger.info("[ADMIN] Fetching weekly activity")
            
            activity_data = await self.stats_service.get_weekly_activity()
            
            response = WeeklyActivityResponse(**activity_data)

            return SuccessResponse(
                message="Weekly activity retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get weekly activity: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve weekly activity: {str(e)}"
            )

    async def get_severity_stats(self, period: str = 'month') -> SuccessResponse[SeverityStatsResponse]:
        """
        Get severity level statistics for bar chart
        """
        try:
            logger.info(f"[ADMIN] Fetching severity level statistics (period: {period})")
            
            severity_data = await self.stats_service.get_severity_stats(period=period)
            
            response = SeverityStatsResponse(**severity_data)

            return SuccessResponse(
                message="Severity statistics retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get severity stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve severity statistics: {str(e)}"
            )

    async def get_system_logs(self, limit: int = 10) -> SuccessResponse[SystemLogsResponse]:
        """
        Get recent system logs and alerts
        """
        try:
            logger.info(f"[ADMIN] Fetching system logs (limit: {limit})")
            
            logs_data = await self.stats_service.get_system_logs(limit=limit)
            
            response = SystemLogsResponse(**logs_data)

            return SuccessResponse(
                message="System logs retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get system logs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve system logs: {str(e)}"
            )
