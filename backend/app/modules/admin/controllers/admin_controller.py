from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
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

    async def get_dashboard_overview(self) -> Union[SuccessResponse[DashboardOverviewResponse], ErrorResponse]:
        """
        Get dashboard overview statistics
        Returns data for all 4 main cards
        """
        try:
            logger.info("[ADMIN] Fetching dashboard overview")
            
            overview_data = await self.stats_service.get_dashboard_overview()
            
            response = DashboardOverviewResponse(**overview_data)

            return SuccessResponse(
                message="Dashboard overview retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get dashboard overview: {e}")
            return ErrorResponse(
                message="Failed to retrieve dashboard overview",
                error_code="DASHBOARD_OVERVIEW_ERROR",
                error_details={"error": str(e)}
            )

    async def get_wound_type_distribution(self) -> Union[SuccessResponse[WoundTypeDistributionResponse], ErrorResponse]:
        """
        Get wound type distribution for pie chart
        """
        try:
            logger.info("[ADMIN] Fetching wound type distribution")
            
            distribution_data = await self.stats_service.get_wound_type_distribution()
            
            response = WoundTypeDistributionResponse(**distribution_data)

            return SuccessResponse(
                message="Wound type distribution retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get wound type distribution: {e}")
            return ErrorResponse(
                message="Failed to retrieve wound type distribution",
                error_code="WOUND_DISTRIBUTION_ERROR",
                error_details={"error": str(e)}
            )

    async def get_weekly_activity(self) -> Union[SuccessResponse[WeeklyActivityResponse], ErrorResponse]:
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
            return ErrorResponse(
                message="Failed to retrieve weekly activity",
                error_code="WEEKLY_ACTIVITY_ERROR",
                error_details={"error": str(e)}
            )

    async def get_severity_stats(self) -> Union[SuccessResponse[SeverityStatsResponse], ErrorResponse]:
        """
        Get severity level statistics for bar chart
        """
        try:
            logger.info("[ADMIN] Fetching severity level statistics")
            
            severity_data = await self.stats_service.get_severity_stats()
            
            response = SeverityStatsResponse(**severity_data)

            return SuccessResponse(
                message="Severity statistics retrieved successfully",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get severity stats: {e}")
            return ErrorResponse(
                message="Failed to retrieve severity statistics",
                error_code="SEVERITY_STATS_ERROR",
                error_details={"error": str(e)}
            )

    async def get_system_logs(self, limit: int = 10) -> Union[SuccessResponse[SystemLogsResponse], ErrorResponse]:
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
            return ErrorResponse(
                message="Failed to retrieve system logs",
                error_code="SYSTEM_LOGS_ERROR",
                error_details={"error": str(e)}
            )
