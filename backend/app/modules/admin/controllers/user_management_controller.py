from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status
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
from app.modules.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class UserManagementController:
    """Controller cho các thao tác quản lý user"""
    
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
        Lấy danh sách user được phân trang với bộ lọc
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
                message="Đã lấy thành công danh sách users",
                data=response_data
            )
        except Exception as e:
            logger.error(f"Không thể lấy danh sách users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy danh sách users: {str(e)}"
            )
    
    async def get_user_detail(self, user_id: str) -> SuccessResponse[UserDetailResponse]:
        """
        Lấy thông tin chi tiết về một user cụ thể
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng user ID không hợp lệ"
            )
        
        try:
            user_detail = await self.service.get_user_detail(user_uuid)
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy user với ID {user_id}"
                )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="Đã lấy thành công chi tiết user",
                data=response_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Không thể lấy chi tiết user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy chi tiết user: {str(e)}"
            )
    
    async def create_user(
        self,
        user_data: CreateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Tạo user mới
        """
        try:
            user_detail = await self.service.create_user(user_data)
            
            await self.audit_service.log_event(
                action="admin_user_create",
                resource_type="user",
                resource_id=str(user_detail["user_id"]),
                success=True,
                details={
                    "email": user_data.email,
                    "user_name": user_data.user_name
                }
            )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="Đã tạo thành công user",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Không thể tạo user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể tạo user: {str(e)}"
            )
    
    async def update_user(
        self,
        user_id: str,
        user_data: UpdateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Cập nhật thông tin user
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng user ID không hợp lệ"
            )
        
        try:
            user_detail = await self.service.update_user(user_uuid, user_data)
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy user với ID {user_id}"
                )
            
            await self.audit_service.log_event(
                action="admin_user_update",
                resource_type="user",
                resource_id=user_id,
                success=True
            )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="Đã cập nhật thành công user",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Không thể cập nhật user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể cập nhật user: {str(e)}"
            )
    
    async def delete_user(self, user_id: str) -> SuccessResponse:
        """
        Xóa user (xóa mềm)
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng user ID không hợp lệ"
            )
        
        try:
            success = await self.service.delete_user(user_uuid)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy user với ID {user_id}"
                )
            
            await self.audit_service.log_event(
                action="admin_user_delete",
                resource_type="user",
                resource_id=user_id,
                success=True
            )
            
            return SuccessResponse(
                message="Đã xóa thành công user",
                data={"user_id": user_id}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Không thể xóa user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể xóa user: {str(e)}"
            )
    
    async def update_user_status(
        self,
        user_id: str,
        status_data: UpdateUserStatusRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Cập nhật trạng thái active của user
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng user ID không hợp lệ"
            )
        
        try:
            user_detail = await self.service.update_user_status(
                user_uuid,
                status_data.is_active
            )
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy user với ID {user_id}"
                )
            
            response_data = UserDetailResponse(user=user_detail)
            
            status_text = "đã kích hoạt" if status_data.is_active else "đã vô hiệu hóa"
            
            return SuccessResponse(
                message=f"User {status_text} thành công",
                data=response_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Không thể cập nhật trạng thái user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể cập nhật trạng thái user: {str(e)}"
            )
    
    async def get_user_stats(self) -> SuccessResponse[UserStatsResponse]:
        """
        Lấy thống kê tổng quan về users
        """
        try:
            stats = await self.service.get_user_stats()
            
            return SuccessResponse(
                message="Đã lấy thành công thống kê users",
                data=stats
            )
        except Exception as e:
            logger.error(f"Không thể lấy thống kê users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể lấy thống kê users: {str(e)}"
            )
    
    async def resend_verification_email(self, user_id: str) -> SuccessResponse:
        """
        Gửi lại email xác thực cho user chưa xác thực
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Định dạng user ID không hợp lệ"
            )
        
        try:
            success = await self.service.resend_verification_email(user_uuid)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy user với ID {user_id} hoặc đã được xác thực"
                )
            
            return SuccessResponse(
                message="Đã gửi thành công email xác thực",
                data={"user_id": user_id}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Không thể gửi lại email xác thực: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không thể gửi lại email xác thực: {str(e)}"
            )
