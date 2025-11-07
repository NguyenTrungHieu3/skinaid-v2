from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status

from app.modules.admin.services.user_management_service import UserManagementService
from app.modules.admin.schemas.user_management_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserDetailResponse,
    UserStatsResponse
)
from app.shared.schemas.response import SuccessResponse, ErrorResponse


class UserManagementController:
    """Controller for user management operations"""
    
    def __init__(self, db: AsyncSession):
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
            return ErrorResponse(
                message="Failed to retrieve users",
                error=str(e)
            )
    
    async def get_user_detail(self, user_id: str) -> SuccessResponse[UserDetailResponse]:
        """
        Get detailed information about a specific user
        """
        try:
            user_uuid = UUID(user_id)
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
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        except HTTPException:
            raise
        except Exception as e:
            return ErrorResponse(
                message="Failed to retrieve user detail",
                error=str(e)
            )
    
    async def create_user(
        self,
        user_data: CreateUserRequest
    ) -> SuccessResponse[UserDetailResponse]:
        """
        Create a new user
        """
        try:
            user_detail = await self.service.create_user(user_data)
            
            response_data = UserDetailResponse(user=user_detail)
            
            return SuccessResponse(
                message="User created successfully",
                data=response_data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            return ErrorResponse(
                message="Failed to create user",
                error=str(e)
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
            user_detail = await self.service.update_user(user_uuid, user_data)
            
            if not user_detail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
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
            return ErrorResponse(
                message="Failed to update user",
                error=str(e)
            )
    
    async def delete_user(self, user_id: str) -> SuccessResponse:
        """
        Delete a user (soft delete)
        """
        try:
            user_uuid = UUID(user_id)
            success = await self.service.delete_user(user_uuid)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            return SuccessResponse(
                message="User deleted successfully",
                data={"user_id": user_id}
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        except HTTPException:
            raise
        except Exception as e:
            return ErrorResponse(
                message="Failed to delete user",
                error=str(e)
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
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        except HTTPException:
            raise
        except Exception as e:
            return ErrorResponse(
                message="Failed to update user status",
                error=str(e)
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
            return ErrorResponse(
                message="Failed to retrieve user statistics",
                error=str(e)
            )
    
    async def resend_verification_email(self, user_id: str) -> SuccessResponse:
        """
        Resend verification email to unverified user
        """
        try:
            user_uuid = UUID(user_id)
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
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        except HTTPException:
            raise
        except Exception as e:
            return ErrorResponse(
                message="Failed to resend verification email",
                error=str(e)
            )
