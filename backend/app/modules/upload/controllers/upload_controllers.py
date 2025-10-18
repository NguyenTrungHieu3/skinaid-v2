from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any, Optional
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.models.upload_logs import UploadLog

logger = logging.getLogger(__name__)

class UploadController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def create_upload_log(
        self,
        user_id: Optional[str],
        file_name: str,
        file_size: int,
        mime_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        upload_status: str = "pending"
    ) -> UploadLog:
        """Tạo upload log mới."""
        upload_log = UploadLog.create_log(
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            upload_status=upload_status,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(upload_log)
        await self.db.commit()
        await self.db.refresh(upload_log)

        logger.info(f"Created upload log: {upload_log.upload_log_id}")
        return upload_log

    async def get_upload_logs(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Lấy lịch sử upload của user."""
        try:
            query = UploadLog.__table__.select().where(
                UploadLog.user_id == user_id
            ).order_by(UploadLog.created_at.desc()).limit(limit).offset(offset)

            result = await self.db.execute(query)
            upload_logs = result.fetchall()

            logs_data = [log.to_response_dict() for log in upload_logs]

            return SuccessResponse(
                message="Lấy lịch sử upload thành công",
                data={
                    "logs": logs_data,
                    "total": len(logs_data),
                    "limit": limit,
                    "offset": offset
                }
            )

        except Exception as e:
            logger.error(f"Error getting upload logs: {str(e)}")
            return ErrorResponse(
                message="Có lỗi không mong muốn xảy ra khi lấy lịch sử upload",
                error_code="UPLOAD_LOGS_RETRIEVAL_FAILED",
                error_details=None
            )

    async def update_upload_log_status(
        self,
        upload_log_id: str,
        status: str,
        error_message: Optional[str] = None,
        validation_errors: Optional[Dict[str, Any]] = None,
        analysis_id: Optional[str] = None
    ) -> bool:
        """Cập nhật trạng thái upload log."""
        try:
            # Lấy upload log từ database
            query = UploadLog.__table__.select().where(
                UploadLog.upload_log_id == upload_log_id
            )
            result = await self.db.execute(query)
            upload_log = result.first()

            if not upload_log:
                logger.warning(f"Upload log not found: {upload_log_id}")
                return False

            # Cập nhật trạng thái
            if status == "success":
                upload_log.mark_success()
            else:
                upload_log.mark_failed(error_message or "Unknown error", validation_errors)

            if analysis_id:
                upload_log.update_analysis_id(analysis_id)

            await self.db.commit()
            logger.info(f"Updated upload log {upload_log_id} status to: {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update upload log {upload_log_id}: {e}")
            await self.db.rollback()
            return False

    async def get_upload_statistics(self, user_id: str) -> Dict[str, Any]:
        """Lấy thống kê upload của user."""
        try:
            # Tổng số uploads
            total_query = UploadLog.__table__.select().where(
                UploadLog.user_id == user_id
            )
            total_result = await self.db.execute(total_query)
            total_uploads = len(total_result.fetchall())

            # Thống kê theo trạng thái
            status_counts = {}
            for status in ["pending", "success", "failed"]:
                status_query = UploadLog.__table__.select().where(
                    UploadLog.user_id == user_id,
                    UploadLog.upload_status == status
                )
                status_result = await self.db.execute(status_query)
                status_counts[status] = len(status_result.fetchall())

            return {
                "total_uploads": total_uploads,
                "status_breakdown": status_counts,
                "success_rate": (
                    status_counts.get("success", 0) / total_uploads * 100
                    if total_uploads > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Failed to get upload statistics for {user_id}: {e}")
            return {
                "total_uploads": 0,
                "status_breakdown": {},
                "success_rate": 0
            }