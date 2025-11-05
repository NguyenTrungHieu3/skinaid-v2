from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Union, Dict, Any, Optional
from fastapi import status
import logging
import uuid

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.models.upload_logs import UploadLog

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)


class UploadController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def create_upload_log(
        self,
        user_id: Optional[uuid.UUID],
        file_name: str,
        file_size: int,
        mime_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        upload_status: str = "pending"
    ) -> Union[UploadLog, None]:
        """Create new upload log."""
        try:
            logger.info(
                f"[CREATE_LOG] Creating upload log - "
                f"User: {user_id}, File: {file_name}, Size: {file_size}"
            )
            
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

            logger.info(f"[CREATE_LOG] Success: {upload_log.upload_log_id}")
            return upload_log

        except Exception as e:
            logger.error(f"[CREATE_LOG] Error: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def get_upload_logs(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Get user's upload history."""
        try:
            logger.info(
                f"[GET_LOGS] Getting upload logs - "
                f"User: {user_id}, Limit: {limit}, Offset: {offset}"
            )
            
            # Query upload logs
            query = (
                select(UploadLog)
                .where(UploadLog.user_id == user_id)
                .order_by(UploadLog.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(query)
            upload_logs = result.scalars().all()

            # Convert to dict
            logs_data = [
                {
                    "upload_log_id": str(log.upload_log_id),
                    "file_name": log.file_name,
                    "file_size": log.file_size,
                    "mime_type": log.mime_type,
                    "upload_status": log.upload_status,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    "ip_address": log.ip_address,
                    "error_message": log.error_message
                }
                for log in upload_logs
            ]

            logger.info(f"[GET_LOGS] Success: {len(logs_data)} logs found")
            
            return SuccessResponse(
                message=Message.UPLOAD_LOGS_GET_SUCCESS_MSG,
                data={
                    "logs": logs_data,
                    "total": len(logs_data),
                    "limit": limit,
                    "offset": offset
                }
            )

        except Exception as e:
            logger.error(f"[GET_LOGS] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.UPLOAD_LOGS_UNEXPECTED_ERROR_MSG,
                error_code=ErrorCode.UPLOAD_LOGS_UNEXPECTED_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_upload_log_status(
        self,
        upload_log_id: uuid.UUID,
        upload_status: str,
        error_message: Optional[str] = None,
        validation_errors: Optional[Dict[str, Any]] = None,
        analysis_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Update upload log status."""
        try:
            logger.info(
                f"[UPDATE_LOG] Updating log: {upload_log_id}, "
                f"Status: {upload_status}"
            )
            
            # Get upload log from database
            query = select(UploadLog).where(
                UploadLog.upload_log_id == upload_log_id
            )
            result = await self.db.execute(query)
            upload_log = result.scalar_one_or_none()

            if not upload_log:
                logger.warning(f"[UPDATE_LOG] Upload log not found: {upload_log_id}")
                return False

            # Update status
            if upload_status == "success":
                upload_log.mark_success()
            else:
                upload_log.mark_failed(
                    error_message or "Unknown error",
                    validation_errors
                )

            if analysis_id:
                upload_log.update_analysis_id(analysis_id)

            await self.db.commit()
            
            logger.info(
                f"[UPDATE_LOG] Success: {upload_log_id} → {upload_status}"
            )
            return True

        except Exception as e:
            logger.error(
                f"[UPDATE_LOG] Error updating {upload_log_id}: {e}",
                exc_info=True
            )
            await self.db.rollback()
            return False

    async def get_upload_statistics(
        self,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Get user's upload statistics."""
        try:
            logger.info(f"[STATISTICS] Getting upload stats for user: {user_id}")
            
            # Total uploads count
            total_query = select(func.count()).select_from(UploadLog).where(
                UploadLog.user_id == user_id
            )
            total_result = await self.db.execute(total_query)
            total_uploads = total_result.scalar() or 0

            # Status breakdown
            status_counts = {}
            for status_type in ["pending", "success", "failed"]:
                status_query = select(func.count()).select_from(UploadLog).where(
                    UploadLog.user_id == user_id,
                    UploadLog.upload_status == status_type
                )
                status_result = await self.db.execute(status_query)
                status_counts[status_type] = status_result.scalar() or 0

            # Calculate success rate
            success_rate = (
                (status_counts.get("success", 0) / total_uploads * 100)
                if total_uploads > 0 else 0
            )

            stats_data = {
                "total_uploads": total_uploads,
                "status_breakdown": status_counts,
                "success_rate": round(success_rate, 2)
            }

            logger.info(
                f"[STATISTICS] Success: {user_id} - "
                f"Total: {total_uploads}, Success rate: {success_rate:.2f}%"
            )
            
            return SuccessResponse(
                message=Message.UPLOAD_STATISTICS_SUCCESS_MSG,
                data=stats_data
            )

        except Exception as e:
            logger.error(f"[STATISTICS] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.UPLOAD_STATISTICS_ERROR_MSG,
                error_code=ErrorCode.UPLOAD_STATISTICS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_upload_log_by_id(
        self,
        upload_log_id: uuid.UUID
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Get upload log by ID."""
        try:
            logger.info(f"[GET_LOG] Getting upload log: {upload_log_id}")
            
            query = select(UploadLog).where(
                UploadLog.upload_log_id == upload_log_id
            )
            result = await self.db.execute(query)
            upload_log = result.scalar_one_or_none()

            if not upload_log:
                logger.warning(f"[GET_LOG] Upload log not found: {upload_log_id}")
                return ErrorResponse(
                    message=Message.UPLOAD_LOG_NOT_FOUND_MSG,
                    error_code=ErrorCode.UPLOAD_LOG_NOT_FOUND,
                    error_details={"upload_log_id": str(upload_log_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            log_data = {
                "upload_log_id": str(upload_log.upload_log_id),
                "user_id": str(upload_log.user_id) if upload_log.user_id else None,
                "file_name": upload_log.file_name,
                "file_size": upload_log.file_size,
                "mime_type": upload_log.mime_type,
                "upload_status": upload_log.upload_status,
                "created_at": upload_log.created_at.isoformat() if upload_log.created_at else None,
                "ip_address": upload_log.ip_address,
                "user_agent": upload_log.user_agent,
                "error_message": upload_log.error_message,
                "validation_errors": upload_log.validation_errors,
                "analysis_id": str(upload_log.analysis_id) if upload_log.analysis_id else None
            }

            logger.info(f"[GET_LOG] Success: {upload_log_id}")
            
            return SuccessResponse(
                message=Message.UPLOAD_LOGS_GET_SUCCESS_MSG,
                data=log_data
            )

        except Exception as e:
            logger.error(f"[GET_LOG] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.UPLOAD_LOGS_UNEXPECTED_ERROR_MSG,
                error_code=ErrorCode.UPLOAD_LOGS_UNEXPECTED_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )