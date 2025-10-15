from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import uuid
from datetime import datetime, timezone

from app.modules.upload.models.upload_validations import UploadValidation
from app.modules.upload.schemas.validation import (
    UploadValidationCreate,
    UploadValidationResponse
)

logger = logging.getLogger(__name__)


class UploadValidationService:
    """Service xử lý các thao tác với UploadValidation model"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_validation_record(
        self,
        validation_data: UploadValidationCreate,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UploadValidation:
        """
        Tạo bản ghi validation mới

        Args:
            validation_data: Dữ liệu validation từ client
            request_id: ID của request (tự động tạo nếu không có)
            ip_address: Địa chỉ IP của client
            user_agent: User agent của client

        Returns:
            UploadValidation object đã được tạo
        """
        try:
            sql = text("""
                INSERT INTO upload_validations (upload_validations_id, user_id, file_name, file_size, file_type, validation_passed, validation_errors, ip_address, user_agent, request_id, attempt_count, created_at, updated_at)
                VALUES (:upload_validations_id, :user_id, :file_name, :file_size, :file_type, :validation_passed, :validation_errors, :ip_address, :user_agent, :request_id, :attempt_count, :created_at, :updated_at)
                RETURNING *
            """)

            params = {
                "upload_validations_id": str(uuid.uuid4()),
                "user_id": validation_data.user_id,
                "file_name": validation_data.file_name,
                "file_size": validation_data.file_size,
                "file_type": validation_data.file_type,
                "validation_passed": validation_data.validation_passed,
                "validation_errors": validation_data.validation_errors,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id or str(uuid.uuid4()),
                "attempt_count": 1,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            }

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                raise Exception("Failed to get returning row after insert.")

            return UploadValidation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to create validation record: {e}")
            await self.db.rollback()
            raise

    async def get_validation_by_id(self, validation_id: str) -> Optional[UploadValidation]:
        """
        Lấy validation record theo ID

        Args:
            validation_id: ID của validation record

        Returns:
            UploadValidation object hoặc None nếu không tìm thấy
        """
        try:
            sql = text("""
                SELECT * FROM upload_validations
                WHERE upload_validations_id = :validation_id
            """)

            result = await self.db.execute(sql, {"validation_id": validation_id})
            row = result.mappings().first()

            if not row:
                return None

            return UploadValidation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to get validation by ID {validation_id}: {e}")
            return None

    async def get_validation_by_request_id(self, request_id: str) -> Optional[UploadValidation]:
        """
        Lấy validation record theo request ID

        Args:
            request_id: ID của request

        Returns:
            UploadValidation object hoặc None nếu không tìm thấy
        """
        try:
            sql = text("""
                SELECT * FROM upload_validations
                WHERE request_id = :request_id
            """)

            result = await self.db.execute(sql, {"request_id": request_id})
            row = result.mappings().first()

            if not row:
                return None

            return UploadValidation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to get validation by request ID {request_id}: {e}")
            return None

    async def update_validation_attempt(
        self,
        validation_id: str,
        validation_passed: bool,
        validation_errors: Optional[Dict[str, Any]] = None
    ) -> Optional[UploadValidation]:
        """
        Cập nhật thông tin validation attempt

        Args:
            validation_id: ID của validation record
            validation_passed: Kết quả validation
            validation_errors: Chi tiết lỗi nếu validation thất bại

        Returns:
            UploadValidation object đã được cập nhật hoặc None nếu không tìm thấy
        """
        try:
            sql = text("""
                UPDATE upload_validations
                SET validation_passed = :validation_passed, validation_errors = :validation_errors, attempt_count = attempt_count + 1, updated_at = :updated_at
                WHERE upload_validations_id = :validation_id
                RETURNING *
            """)

            params = {
                "validation_passed": validation_passed,
                "validation_errors": validation_errors,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "validation_id": validation_id
            }

            result = await self.db.execute(sql, params)
            await self.db.commit()
            row = result.mappings().first()

            if not row:
                return None

            return UploadValidation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to update validation {validation_id}: {e}")
            await self.db.rollback()
            return None

    async def get_user_validations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[UploadValidation]:
        """
        Lấy danh sách validation records của user

        Args:
            user_id: ID của user
            limit: Số lượng records tối đa
            offset: Số records bỏ qua

        Returns:
            List các UploadValidation objects
        """
        try:
            sql = text("""
                SELECT * FROM upload_validations
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(sql, {
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            })

            rows = result.mappings().all()
            return [UploadValidation.model_validate(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get user validations for {user_id}: {e}")
            return []

    async def create_validation_response(self, validation) -> UploadValidationResponse:
        """
        Tạo UploadValidationResponse từ UploadValidation model hoặc dictionary

        Args:
            validation: UploadValidation object hoặc dictionary chứa validation data

        Returns:
            UploadValidationResponse object
        """
        # Handle both UploadValidation object and dictionary for backward compatibility
        if hasattr(validation, 'upload_validations_id'):
            # It's a UploadValidation object
            upload_validations_id = validation.upload_validations_id
            user_id = validation.user_id
            file_name = validation.file_name
            file_size = validation.file_size
            file_type = validation.file_type
            validation_passed = validation.validation_passed
            validation_errors = validation.validation_errors
            ip_address = validation.ip_address
            user_agent = validation.user_agent
            request_id = validation.request_id
            attempt_count = validation.attempt_count
            created_at = validation.created_at
            updated_at = validation.updated_at
        else:
            # It's a dictionary
            upload_validations_id = validation.get("upload_validations_id")
            user_id = validation.get("user_id")
            file_name = validation.get("file_name")
            file_size = validation.get("file_size")
            file_type = validation.get("file_type")
            validation_passed = validation.get("validation_passed")
            validation_errors = validation.get("validation_errors")
            ip_address = validation.get("ip_address")
            user_agent = validation.get("user_agent")
            request_id = validation.get("request_id")
            attempt_count = validation.get("attempt_count")
            created_at = validation.get("created_at")
            updated_at = validation.get("updated_at")

        # Use the new to_response_dict method if available
        if hasattr(validation, 'to_response_dict'):
            return UploadValidationResponse(**validation.to_response_dict())
        else:
            # Fallback for backward compatibility
            return UploadValidationResponse(
                upload_validations_id=upload_validations_id,
                user_id=user_id,
                file_name=file_name,
                file_size=file_size,
                file_type=file_type,
                validation_passed=validation_passed,
                validation_errors=validation_errors,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                attempt_count=attempt_count,
                created_at=created_at,
                updated_at=updated_at
            )