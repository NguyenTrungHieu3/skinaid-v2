from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.services.upload_validation_service import UploadValidationService
from app.modules.upload.schemas.validation import (
    UploadValidationCreate,
    UploadValidationResponse
)
from app.api.v1.deps import get_current_active_user
from app.modules.auth.models.user import User

logger = logging.getLogger(__name__)


class UploadValidationController:
    """Controller xử lý các yêu cầu liên quan đến upload validation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validation_service = UploadValidationService(db)

    async def create_validation_record(
        self,
        validation_data: UploadValidationCreate,
        current_user: User,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SuccessResponse[UploadValidationResponse]:
        """
        Tạo bản ghi validation mới

        Args:
            validation_data: Dữ liệu validation từ client
            current_user: User hiện tại đang đăng nhập
            request_id: ID của request
            ip_address: Địa chỉ IP của client
            user_agent: User agent của client

        Returns:
            SuccessResponse với validation data
        """
        try:
            # Set user_id từ current_user nếu không được cung cấp
            if not validation_data.user_id:
                validation_data.user_id = current_user.user_id

            validation_record = await self.validation_service.create_validation_record(
                validation_data=validation_data,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            validation_response = await self.validation_service.create_validation_response(
                validation_record
            )

            return SuccessResponse(
                message="Tạo bản ghi validation thành công",
                data=validation_response
            )

        except Exception as e:
            logger.error(f"Failed to create validation record: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể tạo bản ghi validation"
            )

    async def get_validation_by_id(
        self,
        validation_id: str,
        current_user: User
    ) -> SuccessResponse[UploadValidationResponse]:
        """
        Lấy thông tin validation theo ID

        Args:
            validation_id: ID của validation record
            current_user: User hiện tại đang đăng nhập

        Returns:
            SuccessResponse với validation data
        """
        try:
            validation_record = await self.validation_service.get_validation_by_id(validation_id)

            if not validation_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy validation record với ID: {validation_id}"
                )

            # Kiểm tra quyền truy cập (chỉ user sở hữu hoặc admin)
            if validation_record.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Không có quyền truy cập validation record này"
                )

            validation_response = await self.validation_service.create_validation_response(
                validation_record
            )

            return SuccessResponse(
                message="Lấy thông tin validation thành công",
                data=validation_response
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get validation by ID {validation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lấy thông tin validation"
            )

    async def get_validation_by_request_id(
        self,
        request_id: str,
        current_user: User
    ) -> SuccessResponse[UploadValidationResponse]:
        """
        Lấy thông tin validation theo request ID

        Args:
            request_id: ID của request
            current_user: User hiện tại đang đăng nhập

        Returns:
            SuccessResponse với validation data
        """
        try:
            validation_record = await self.validation_service.get_validation_by_request_id(request_id)

            if not validation_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy validation record với request ID: {request_id}"
                )

            # Kiểm tra quyền truy cập
            if validation_record.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Không có quyền truy cập validation record này"
                )

            validation_response = await self.validation_service.create_validation_response(
                validation_record
            )

            return SuccessResponse(
                message="Lấy thông tin validation thành công",
                data=validation_response
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get validation by request ID {request_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lấy thông tin validation"
            )

    async def get_user_validations(
        self,
        current_user: User,
        limit: int = 20,
        offset: int = 0
    ) -> SuccessResponse[List[UploadValidationResponse]]:
        """
        Lấy danh sách validation records của user hiện tại

        Args:
            current_user: User hiện tại đang đăng nhập
            limit: Số lượng records tối đa
            offset: Số records bỏ qua

        Returns:
            SuccessResponse với danh sách validation data
        """
        try:
            validation_records = await self.validation_service.get_user_validations(
                user_id=current_user.user_id,
                limit=limit,
                offset=offset
            )

            validation_responses = []
            for record in validation_records:
                response = await self.validation_service.create_validation_response(record)
                validation_responses.append(response)

            return SuccessResponse(
                message="Lấy danh sách validation thành công",
                data=validation_responses
            )

        except Exception as e:
            logger.error(f"Failed to get user validations for {current_user.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lấy danh sách validation"
            )

    async def update_validation_attempt(
        self,
        validation_id: str,
        validation_passed: bool,
        validation_errors: Optional[Dict[str, Any]] = None,
        current_user: User = None
    ) -> SuccessResponse[UploadValidationResponse]:
        """
        Cập nhật thông tin validation attempt

        Args:
            validation_id: ID của validation record
            validation_passed: Kết quả validation
            validation_errors: Chi tiết lỗi nếu validation thất bại
            current_user: User hiện tại đang đăng nhập

        Returns:
            SuccessResponse với validation data đã được cập nhật
        """
        try:
            # Nếu có current_user, kiểm tra quyền truy cập
            if current_user:
                validation_record = await self.validation_service.get_validation_by_id(validation_id)
                if validation_record and validation_record.user_id != current_user.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Không có quyền cập nhật validation record này"
                    )

            updated_validation = await self.validation_service.update_validation_attempt(
                validation_id=validation_id,
                validation_passed=validation_passed,
                validation_errors=validation_errors
            )

            if not updated_validation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy validation record với ID: {validation_id}"
                )

            validation_response = await self.validation_service.create_validation_response(
                updated_validation
            )

            return SuccessResponse(
                message="Cập nhật validation thành công",
                data=validation_response
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update validation {validation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể cập nhật validation"
            )