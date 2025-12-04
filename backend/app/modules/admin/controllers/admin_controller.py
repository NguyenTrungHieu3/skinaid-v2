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
    """Controller cho các endpoint dashboard admin"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stats_service = StatisticsService(db)

    async def get_dashboard_overview(self, period: str = 'month') -> SuccessResponse[DashboardOverviewResponse]:
        """
        Lấy thống kê tổng quan dashboard
        Trả về dữ liệu cho tất cả 4 thẻ chính
        """
        try:
            logger.info(f"[ADMIN] Đang lấy tổng quan dashboard (kỳ: {period})")
            
            overview_data = await self.stats_service.get_dashboard_overview(period=period)
            
            response = DashboardOverviewResponse(**overview_data)

            return SuccessResponse(
                message="Lấy tổng quan dashboard thành công",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Thất bại khi lấy tổng quan dashboard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy tổng quan dashboard: {str(e)}"
            )

    async def get_wound_type_distribution(self, period: str = 'month') -> SuccessResponse[WoundTypeDistributionResponse]:
        """
        Lấy phân bố loại vết thương cho biểu đồ tròn
        """
        try:
            logger.info(f"[ADMIN] Đang lấy phân bố loại vết thương (kỳ: {period})")
            
            distribution_data = await self.stats_service.get_wound_type_distribution(period=period)
            
            response = WoundTypeDistributionResponse(**distribution_data)

            return SuccessResponse(
                message="Lấy phân bố loại vết thương thành công",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Thất bại khi lấy phân bố loại vết thương: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy phân bố loại vết thương: {str(e)}"
            )

    async def get_weekly_activity(self) -> SuccessResponse[WeeklyActivityResponse]:
        """
        Lấy thống kê hoạt động hàng tuần cho biểu đồ cột
        """
        try:
            logger.info("[ADMIN] Đang lấy hoạt động hàng tuần")
            
            activity_data = await self.stats_service.get_weekly_activity()
            
            response = WeeklyActivityResponse(**activity_data)

            return SuccessResponse(
                message="Lấy hoạt động hàng tuần thành công",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Thất bại khi lấy hoạt động hàng tuần: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy hoạt động hàng tuần: {str(e)}"
            )

    async def get_severity_stats(self, period: str = 'month') -> SuccessResponse[SeverityStatsResponse]:
        """
        Lấy thống kê mức độ nghiêm trọng cho biểu đồ cột
        """
        try:
            logger.info(f"[ADMIN] Đang lấy thống kê mức độ nghiêm trọng (kỳ: {period})")
            
            severity_data = await self.stats_service.get_severity_stats(period=period)
            
            response = SeverityStatsResponse(**severity_data)

            return SuccessResponse(
                message="Lấy thống kê mức độ nghiêm trọng thành công",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Thất bại khi lấy thống kê mức độ nghiêm trọng: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy thống kê mức độ nghiêm trọng: {str(e)}"
            )

    async def get_system_logs(self, limit: int = 10) -> SuccessResponse[SystemLogsResponse]:
        """
        Lấy logs hệ thống và cảnh báo gần đây
        """
        try:
            logger.info(f"[ADMIN] Đang lấy logs hệ thống (giới hạn: {limit})")
            
            logs_data = await self.stats_service.get_system_logs(limit=limit)
            
            response = SystemLogsResponse(**logs_data)

            return SuccessResponse(
                message="Lấy logs hệ thống thành công",
                data=response
            )

        except Exception as e:
            logger.error(f"[ADMIN] Thất bại khi lấy logs hệ thống: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy logs hệ thống: {str(e)}"
            )
