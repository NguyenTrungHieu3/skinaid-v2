import logging
from typing import Union
from datetime import datetime
from fastapi import status

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.services.audit_service import AuditService
from app.modules.audit.schemas.audit_schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditStatsResponse,
    AuditLogFilterParams
)
from app.shared.schemas.response import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)


class AuditController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)

    async def get_audit_logs(
        self,
        filters: AuditLogFilterParams
    ) -> Union[SuccessResponse[AuditLogListResponse], ErrorResponse]:

        try:
            offset = (filters.page - 1) * filters.limit

            logger.info(
                f"[GET_AUDIT_LOGS] Đang lấy logs: "
                f"trang={filters.page}, giới hạn={filters.limit}"
            )

            # Lấy logs và tổng số từ service
            logs, total_count = await self.audit_service.get_audit_logs(
                user_id=filters.user_id,
                action=filters.action,
                resource_type=filters.resource_type,
                success=filters.success,
                is_guest=filters.is_guest,
                start_date=filters.start_date,
                end_date=filters.end_date,
                limit=filters.limit,
                offset=offset
            )

            # Chuyển đổi sang AuditLogResponse (dùng to_dict())
            audit_logs = [
                AuditLogResponse(**log.to_dict())
                for log in logs
            ]

            # Tính toán metadata phân trang
            total_pages = (total_count + filters.limit - 1) // filters.limit
            has_more = filters.page < total_pages

            # Tạo response data
            response_data = AuditLogListResponse(
                logs=audit_logs,
                total=total_count,
                page=filters.page,
                limit=filters.limit,
                total_pages=total_pages,
                has_more=has_more
            )

            logger.info(
                f"[GET_AUDIT_LOGS] Thành công: "
                f"trả về {len(audit_logs)}/{total_count} logs"
            )

            return SuccessResponse(
                message="Lấy danh sách audit logs thành công",
                data=response_data
            )

        except Exception as e:
            logger.error(
                f"[GET_AUDIT_LOGS] Lỗi: {str(e)}",
                exc_info=True
            )
            return ErrorResponse(
                message="Lỗi khi lấy danh sách audit logs",
                error="INTERNAL_SERVER_ERROR",
                error_details={"error": str(e), "context": "get_audit_logs"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_audit_stats(
        self
    ) -> Union[SuccessResponse[AuditStatsResponse], ErrorResponse]:
        try:
            logger.info("[GET_AUDIT_STATS] Đang lấy thống kê")

            # Lấy thống kê từ service
            stats_data = await self.audit_service.get_audit_stats()

            # Tạo response
            response_data = AuditStatsResponse(
                total_logs=stats_data['total_logs'],
                success_rate=stats_data['success_rate'],
                action_distribution=stats_data['action_distribution'],
                recent_activity_24h=stats_data['recent_activity_24h']
            )

            logger.info(
                f"[GET_AUDIT_STATS] Thành công: "
                f"{stats_data['total_logs']} tổng logs, "
                f"{stats_data['success_rate']}% tỷ lệ thành công"
            )

            return SuccessResponse(
                message="Lấy thống kê audit thành công",
                data=response_data
            )

        except Exception as e:
            logger.error(
                f"[GET_AUDIT_STATS] Lỗi: {str(e)}",
                exc_info=True
            )
            return ErrorResponse(
                message="Lỗi khi lấy thống kê audit",
                error="INTERNAL_SERVER_ERROR",
                error_details={"error": str(e), "context": "get_audit_stats"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def health_check(self) -> SuccessResponse[dict]:
        logger.debug("[HEALTH] Đang kiểm tra audit service")
        
        return SuccessResponse(
            message="Audit service đang hoạt động tốt",
            data={
                "service": "audit",
                "status": "healthy",
                "features": {
                    "audit_logging": True,
                    "statistics": True,
                    "filtering": True,
                    "pagination": True,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )