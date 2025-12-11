from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status as http_status
import logging

from app.modules.admin.services.user_management_service import UserManagementService
from app.modules.admin.schemas.user_management_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserDetailResponse,
    UserStatsResponse
)
from app.shared.schemas.response import SuccessResponse
from app.utils.logging_utils import sanitize_user_data, log_admin_action
from app.utils.decorators import handle_admin_errors
from app.modules.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class UserManagementController:
    """Controller cho các hoạt động quản lý người dùng"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
        self.service = UserManagementService(db)
    
    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> SuccessResponse[UserListResponse]:
        """
        Lấy danh sách người dùng có phân trang và bộ lọc
        """
        try:
            users, pagination = await self.service.get_users(
                page=page,
                limit=limit,
                search=search,
                role=role,
                status=status
            )
            
            response_data = UserListResponse(
                users=users,
                pagination=pagination
            )
            
            return SuccessResponse(
                message="Lấy danh sách người dùng thành công",
                data=response_data
            )
        except Exception as e:
            logger.error(f"Thất bại khi lấy danh sách người dùng: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy danh sách người dùng: {str(e)}"
            )
    
    async def get_user_detail(self, user_id: str) -> SuccessResponse[UserDetailResponse]:
        """
        Lấy thông tin chi tiết về một người dùng cụ thể
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Định dạng ID người dùng không hợp lệ"
            )
        
        try:
            user_detail = await self.service.get_user_detail(user_uuid)
            
            if not user_detail:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy người dùng với ID {user_id}"
                )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="Lấy chi tiết người dùng thành công",
                data=response_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Thất bại khi lấy chi tiết người dùng: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy chi tiết người dùng: {str(e)}"
            )
    
    async def create_user(
        self,
        user_data: CreateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Tạo người dùng mới
        """
        try:
            # Log sanitized user creation (mật khẩu sẽ được ẩn)
            sanitized_data = sanitize_user_data(user_data.dict())
            logger.info(log_admin_action("CREATE_USER", user_data.email, sanitized_data))
            
            user_detail = await self.service.create_user(user_data)
            
            await self.audit_service.log_event(
                action="admin_user_create",
                resource_type="user",
                resource_id=str(user_detail.user_id),
                success=True,
                details={
                    "email": user_data.email,
                    "user_name": user_data.display_name  # Use display_name as user_name might not be in request
                }
            )
            
            response_data = UserDetailResponse(user=user_detail)
            
            logger.info(f"Tạo người dùng thành công: {user_detail.user_id}")
            
            return SuccessResponse(
                message="Tạo người dùng thành công",
                data=response_data
            )
        except ValueError as e:
            logger.warning(f"Thất bại khi tạo người dùng (lỗi validation): {str(e)}")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Thất bại khi tạo người dùng: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể tạo người dùng: {str(e)}"
            )
    
    async def update_user(
        self,
        user_id: str,
        user_data: UpdateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Cập nhật thông tin người dùng
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Định dạng ID người dùng không hợp lệ"
            )
        
        try:
            user_detail = await self.service.update_user(user_uuid, user_data)
            
            if not user_detail:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy người dùng với ID {user_id}"
                )
            
            await self.audit_service.log_event(
                action="admin_user_update",
                resource_type="user",
                resource_id=user_id,
                success=True
            )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="Cập nhật người dùng thành công",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Thất bại khi cập nhật người dùng: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể cập nhật người dùng: {str(e)}"
            )
    
    @handle_admin_errors("delete_user")
    async def delete_user(self, user_id: str) -> SuccessResponse:
        """
        Xóa người dùng (soft delete)
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Định dạng ID người dùng không hợp lệ"
            )
        
        logger.info(log_admin_action("DELETE_USER", user_id))
        
        success = await self.service.delete_user(user_uuid)
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy người dùng với ID {user_id}"
            )
        
        logger.info(f"Xóa người dùng thành công: {user_id}")
        
        return SuccessResponse(
            message="Xóa người dùng thành công",
            data={"user_id": user_id}
        )
    
    async def update_user_status(
        self,
        user_id: str,
        status_data: UpdateUserStatusRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Cập nhật trạng thái hoạt động của người dùng
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Định dạng ID người dùng không hợp lệ"
            )
        
        try:
            user_detail = await self.service.update_user_status(
                user_uuid,
                status_data.is_active
            )
            
            if not user_detail:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy người dùng với ID {user_id}"
                )
            
            response_data = UserDetailResponse(user=user_detail)
            
            status_text = "kích hoạt" if status_data.is_active else "vô hiệu hóa"
            
            return SuccessResponse(
                message=f"Người dùng đã được {status_text} thành công",
                data=response_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Thất bại khi cập nhật trạng thái người dùng: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể cập nhật trạng thái người dùng: {str(e)}"
            )
    
    async def get_user_stats(self) -> SuccessResponse[UserStatsResponse]:
        """
        Lấy thống kê tổng quan về người dùng
        """
        try:
            stats = await self.service.get_user_stats()
            
            return SuccessResponse(
                message="Lấy thống kê người dùng thành công",
                data=stats
            )
        except Exception as e:
            logger.error(f"Thất bại khi lấy thống kê người dùng: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy thống kê người dùng: {str(e)}"
            )
    
    async def resend_verification_email(self, user_id: str) -> SuccessResponse:
        """
        Gửi lại email xác thực cho người dùng chưa xác thực
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Định dạng ID người dùng không hợp lệ"
            )
        
        try:
            success = await self.service.resend_verification_email(user_uuid)
            
            if not success:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy người dùng với ID {user_id} hoặc đã được xác thực"
                )
            
            return SuccessResponse(
                message="Gửi email xác thực thành công",
                data={"user_id": user_id}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Thất bại khi gửi lại email xác thực: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể gửi lại email xác thực: {str(e)}"
            )
