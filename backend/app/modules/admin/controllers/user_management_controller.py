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
from app.utils.logging_utils import sanitize_user_data, log_admin_action
from app.utils.decorators import handle_admin_errors
from app.modules.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class UserManagementController:
    """Controller for user management operations"""
    
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
        Get paginated list of users with filters
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
                message="Users retrieved successfully",
                data=response_data
            )
        except Exception as e:
            logger.error(f"Failed to retrieve users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve users: {str(e)}"
            )
    
    async def get_user_detail(self, user_id: str) -> SuccessResponse[UserDetailResponse]:
        """
        Get detailed information about a specific user
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        try:
            user_detail = await self.service.get_user_detail(user_uuid)
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="User detail retrieved successfully",
                data=response_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve user detail: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user detail: {str(e)}"
            )
    
    async def create_user(
        self,
        user_data: CreateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Create a new user
        """
        try:
            # Log sanitized user creation (password will be redacted)
            sanitized_data = sanitize_user_data(user_data.dict())
            logger.info(log_admin_action("CREATE_USER", user_data.email, sanitized_data))
            
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
            
            logger.info(f"Successfully created user: {user_detail.get('user_id')}")
            
            return SuccessResponse(
                message="User created successfully",
                data=response_data
            )
        except ValueError as e:
            logger.warning(f"Failed to create user (validation error): {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def update_user(
        self,
        user_id: str,
        user_data: UpdateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Update user information
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        try:
            user_detail = await self.service.update_user(user_uuid, user_data)
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            await self.audit_service.log_event(
                action="admin_user_update",
                resource_type="user",
                resource_id=user_id,
                success=True
            )
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="User updated successfully",
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
            logger.error(f"Failed to update user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )
    
    @handle_admin_errors("delete_user")
    async def delete_user(self, user_id: str) -> SuccessResponse:
        """
        Delete a user (soft delete)
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        logger.info(log_admin_action("DELETE_USER", user_id))
        
        success = await self.service.delete_user(user_uuid)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        logger.info(f"Successfully deleted user: {user_id}")
        
        return SuccessResponse(
            message="User deleted successfully",
            data={"user_id": user_id}
        )
    
    async def update_user_status(
        self,
        user_id: str,
        status_data: UpdateUserStatusRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Update user active status
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        try:
            user_detail = await self.service.update_user_status(
                user_uuid,
                status_data.is_active
            )
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            response_data = UserDetailResponse(user=user_detail)
            
            status_text = "activated" if status_data.is_active else "deactivated"
            
            return SuccessResponse(
                message=f"User {status_text} successfully",
                data=response_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update user status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user status: {str(e)}"
            )
    
    async def get_user_stats(self) -> SuccessResponse[UserStatsResponse]:
        """
        Get overall user statistics
        """
        try:
            stats = await self.service.get_user_stats()
            
            return SuccessResponse(
                message="User statistics retrieved successfully",
                data=stats
            )
        except Exception as e:
            logger.error(f"Failed to retrieve user statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user statistics: {str(e)}"
            )
    
    async def resend_verification_email(self, user_id: str) -> SuccessResponse:
        """
        Resend verification email to unverified user
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        try:
            success = await self.service.resend_verification_email(user_uuid)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found or already verified"
                )
            
            return SuccessResponse(
                message="Verification email sent successfully",
                data={"user_id": user_id}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to resend verification email: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resend verification email: {str(e)}"
            )
