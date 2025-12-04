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
from app.core.dependencies import get_db, require_admin
from app.modules.auth.models.user import User
from app.core.database import get_session

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


async def get_admin_controller(db: AsyncSession = Depends(get_db)) -> AdminController:
    """Dependency để lấy admin controller instance"""
    return AdminController(db)


@router.get(
    "/dashboard/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Lấy tổng quan Dashboard",
    description="Lấy thống kê tổng quan cho dashboard admin (4 thẻ chính)"
)
async def get_dashboard_overview(
    period: str = Query("month", enum=["day", "week", "month", "year", "all"], description="Khoảng thời gian thống kê"),
    controller: AdminController = Depends(get_admin_controller),
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
    return await controller.get_dashboard_overview(period=period)


@router.get(
    "/wound-types/distribution",
    response_model=SuccessResponse[WoundTypeDistributionResponse],
    summary="Lấy phân bố loại vết thương",
    description="Lấy phân bố các loại vết thương cho biểu đồ tròn"
)
async def get_wound_type_distribution(
    period: str = Query("month", enum=["day", "week", "month", "year", "all"], description="Khoảng thời gian thống kê"),
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy dữ liệu phân bố loại vết thương cho biểu đồ tròn:
    - Tên loại vết thương (Trầy xước, Bỏng, Bầm tím, v.v.)
    - Số lượng cho mỗi loại
    - Màu hiển thị
    
    **Yêu cầu quyền admin**
    """
    return await controller.get_wound_type_distribution(period=period)


@router.get(
    "/activity/weekly",
    response_model=SuccessResponse[WeeklyActivityResponse],
    summary="Lấy hoạt động hàng tuần",
    description="Lấy thống kê hoạt động hàng tuần cho biểu đồ cột (7 ngày qua)"
)
async def get_weekly_activity(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê hoạt động hàng tuần cho biểu đồ cột:
    - Số lượng upload hàng ngày
    - Số lượng phân tích hàng ngày
    - Dữ liệu 7 ngày qua
    
    **Yêu cầu quyền admin**
    """
    return await controller.get_weekly_activity()


@router.get(
    "/severity/stats",
    response_model=SuccessResponse[SeverityStatsResponse],
    summary="Lấy thống kê mức độ nghiêm trọng",
    description="Lấy phân bố mức độ nghiêm trọng của vết thương (Nhẹ, Trung bình, Nặng)"
)
async def get_severity_stats(
    period: str = Query("month", enum=["day", "week", "month", "year", "all"], description="Khoảng thời gian thống kê"),
    controller: AdminController = Depends(get_admin_controller),
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
    return await controller.get_severity_stats(period=period)


@router.get(
    "/logs/recent",
    response_model=SuccessResponse[SystemLogsResponse],
    summary="Lấy logs hệ thống gần đây",
    description="Lấy logs hệ thống và cảnh báo gần đây để giám sát"
)
async def get_system_logs(
    limit: int = Query(10, ge=1, le=50, description="Số lượng logs cần lấy"),
    controller: AdminController = Depends(get_admin_controller),
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
    return await controller.get_system_logs(limit=limit)


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
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
