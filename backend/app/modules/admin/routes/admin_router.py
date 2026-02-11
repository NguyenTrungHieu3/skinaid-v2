from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.response import SuccessResponse
from app.modules.admin.services.statistics_service import StatisticsService
from app.modules.admin.schemas.admin_schemas import (
    DashboardOverviewResponse,
    WoundTypeDistributionResponse,
    WeeklyActivityResponse,
    SystemLogsResponse,
    SeverityStatsResponse
)
from app.core.dependencies import get_db, require_admin
from app.modules.auth.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


def get_statistics_service(db: AsyncSession = Depends(get_db)) -> StatisticsService:
    """Dependency to get StatisticsService instance"""
    return StatisticsService(db)


@router.get(
    "/dashboard/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Lấy tổng quan Dashboard",
    description="Lấy thống kê tổng quan cho dashboard admin (4 thẻ chính)"
)
async def get_dashboard_overview(
    period: str = Query("month", enum=[
                        "day", "week", "month", "year", "all"], description="Khoảng thời gian thống kê"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê tổng quan dashboard bao gồm:
    - Tổng số người dùng và người dùng hoạt động hôm nay
    - Tổng số ảnh và số lượng đã phân tích
    - Chỉ số độ chính xác của mô hình
    - Thống kê phiên làm việc

    **Yêu cầu quyền admin**
    """
    data = await service.get_dashboard_overview(period=period)
    response = DashboardOverviewResponse(**data)
    return SuccessResponse(
        message="Lấy tổng quan dashboard thành công",
        data=response
    )


@router.get(
    "/wound-types/distribution",
    response_model=SuccessResponse[WoundTypeDistributionResponse],
    summary="Lấy phân bố loại vết thương",
    description="Lấy phân bố các loại vết thương cho biểu đồ tròn"
)
async def get_wound_type_distribution(
    period: str = Query("month", enum=[
                        "day", "week", "month", "year", "all"], description="Khoảng thời gian thống kê"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Lấy dữ liệu phân bố loại vết thương cho biểu đồ tròn:
    - Tên loại vết thương (Trầy xước, Bỏng, Bầm tím, v.v.)
    - Số lượng cho mỗi loại
    - Màu hiển thị

    **Yêu cầu quyền admin**
    """
    data = await service.get_wound_type_distribution(period=period)
    response = WoundTypeDistributionResponse(**data)
    return SuccessResponse(
        message="Lấy phân bố loại vết thương thành công",
        data=response
    )


@router.get(
    "/activity/weekly",
    response_model=SuccessResponse[WeeklyActivityResponse],
    summary="Lấy hoạt động hàng tuần",
    description="Lấy thống kê hoạt động hàng tuần cho biểu đồ cột (7 ngày qua)"
)
async def get_weekly_activity(
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê hoạt động hàng tuần cho biểu đồ cột:
    - Số lượng upload hàng ngày
    - Số lượng phân tích hàng ngày
    - Dữ liệu 7 ngày qua

    **Yêu cầu quyền admin**
    """
    data = await service.get_weekly_activity()
    response = WeeklyActivityResponse(**data)
    return SuccessResponse(
        message="Lấy hoạt động hàng tuần thành công",
        data=response
    )


@router.get(
    "/severity/stats",
    response_model=SuccessResponse[SeverityStatsResponse],
    summary="Lấy thống kê mức độ nghiêm trọng",
    description="Lấy phân bố mức độ nghiêm trọng của vết thương (Nhẹ, Trung bình, Nặng)"
)
async def get_severity_stats(
    period: str = Query("month", enum=[
                        "day", "week", "month", "year", "all"], description="Khoảng thời gian thống kê"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê mức độ nghiêm trọng cho biểu đồ cột:
    - Số lượng vết thương nhẹ
    - Số lượng vết thương trung bình
    - Số lượng vết thương nặng
    - Tổng số phát hiện

    **Yêu cầu quyền admin**
    """
    data = await service.get_severity_stats(period=period)
    response = SeverityStatsResponse(**data)
    return SuccessResponse(
        message="Lấy thống kê mức độ nghiêm trọng thành công",
        data=response
    )


@router.get(
    "/logs/recent",
    response_model=SuccessResponse[SystemLogsResponse],
    summary="Lấy logs hệ thống gần đây",
    description="Lấy logs hệ thống và cảnh báo gần đây để giám sát"
)
async def get_system_logs(
    limit: int = Query(10, ge=1, le=50, description="Số lượng logs cần lấy"),
    service: StatisticsService = Depends(get_statistics_service),
    current_user: User = Depends(require_admin)
):
    """
    Lấy logs hệ thống và cảnh báo gần đây:
    - Logs lỗi
    - Thông báo cảnh báo
    - Thông báo thông tin
    - Sự kiện thành công

    **Yêu cầu quyền admin**
    """
    data = await service.get_system_logs(limit=limit)
    response = SystemLogsResponse(**data)
    return SuccessResponse(
        message="Lấy logs hệ thống thành công",
        data=response
    )


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Kiểm tra sức khỏe dịch vụ Admin",
    description="Kiểm tra xem dịch vụ admin có hoạt động tốt không"
)
async def admin_health_check():
    """Endpoint kiểm tra sức khỏe cho dịch vụ admin"""
    return SuccessResponse(
        message="Dịch vụ admin hoạt động tốt",
        data={
            "status": "healthy",
            "service": "admin_dashboard",
            "version": "1.0.0"
        }
    )
