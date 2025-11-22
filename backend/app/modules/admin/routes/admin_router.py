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
    """Dependency để lấy instance admin controller"""
    return AdminController(db)


@router.get(
    "/dashboard/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Lấy Tổng quan Dashboard",
    description="Lấy thống kê tổng quan cho dashboard admin (4 thẻ chính)"
)
async def get_dashboard_overview(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê tổng quan dashboard bao gồm:
    - Tổng số users và active hôm nay
    - Tổng số images và số đã phân tích
    - Các chỉ số độ chính xác model
    - Thống kê session
    
    **Yêu cầu vai trò admin**
    """
    return await controller.get_dashboard_overview()


@router.get(
    "/wound-types/distribution",
    response_model=SuccessResponse[WoundTypeDistributionResponse],
    summary="Lấy Phân bố Loại Vết thương",
    description="Lấy phân bố các loại vết thương để hiển thị biểu đồ tròn"
)
async def get_wound_type_distribution(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy dữ liệu phân bố loại vết thương cho biểu đồ tròn:
    - Tên các loại vết thương (Trầy xước, Bỏng, Bầm tím, v.v.)
    - Số lượng cho mỗi loại
    - Màu hiển thị
    
    **Yêu cầu vai trò admin**
    """
    return await controller.get_wound_type_distribution()


@router.get(
    "/activity/weekly",
    response_model=SuccessResponse[WeeklyActivityResponse],
    summary="Lấy Hoạt động Hàng tuần",
    description="Lấy thống kê hoạt động hàng tuần cho biểu đồ cột (7 ngày gần đây)"
)
async def get_weekly_activity(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê hoạt động hàng tuần cho biểu đồ cột:
    - Số lượng upload hàng ngày
    - Số lượng phân tích hàng ngày
    - Dữ liệu 7 ngày gần đây
    
    **Yêu cầu vai trò admin**
    """
    return await controller.get_weekly_activity()


@router.get(
    "/severity/stats",
    response_model=SuccessResponse[SeverityStatsResponse],
    summary="Lấy Thống kê Mức độ Nghiêm trọng",
    description="Lấy phân bố mức độ nghiêm trọng vết thương (Nhẹ, Trung bình, Nặng)"
)
async def get_severity_stats(
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê mức độ nghiêm trọng cho biểu đồ cột:
    - Số lượng vết thương nhẹ
    - Số lượng vết thương trung bình
    - Số lượng vết thương nặng
    - Tổng số phát hiện
    
    **Yêu cầu vai trò admin**
    """
    return await controller.get_severity_stats()


@router.get(
    "/logs/recent",
    response_model=SuccessResponse[SystemLogsResponse],
    summary="Lấy Logs Hệ thống Gần đây",
    description="Lấy logs và cảnh báo hệ thống gần đây để giám sát"
)
async def get_system_logs(
    limit: int = Query(10, ge=1, le=50, description="Số lượng logs để lấy"),
    controller: AdminController = Depends(get_admin_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy logs và cảnh báo hệ thống gần đây:
    - Logs lỗi
    - Thông điệp cảnh báo
    - Thông báo thông tin
    - Sự kiện thành công
    
    **Yêu cầu vai trò admin**
    """
    return await controller.get_system_logs(limit=limit)


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Kiểm tra Sức khỏe Dịch vụ Admin",
    description="Kiểm tra xem dịch vụ admin có khỏe mạnh không"
)
async def admin_health_check():
    """Endpoint kiểm tra sức khỏe cho dịch vụ admin"""
    return SuccessResponse(
        message="Dịch vụ admin hoạt động bình thường",
        data={
            "status": "healthy",
            "service": "admin_dashboard",
            "version": "1.0.0"
        }
    )
