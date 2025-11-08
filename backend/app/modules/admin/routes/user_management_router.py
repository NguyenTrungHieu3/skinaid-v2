from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.shared.schemas.response import SuccessResponse
from app.modules.admin.controllers.user_management_controller import UserManagementController
from app.modules.admin.schemas.user_management_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserDetailResponse,
    UserStatsResponse
)
from app.api.v1.deps import get_db, require_admin
from app.modules.auth.models.user import User

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


async def get_user_controller(db: AsyncSession = Depends(get_db)) -> UserManagementController:
    """Dependency to get user management controller instance"""
    return UserManagementController(db)


@router.get(
    "",
    response_model=SuccessResponse[UserListResponse],
    summary="Get Users List",
    description="Get paginated list of users with optional filters"
)
async def get_users(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of users per page"),
    search: Optional[str] = Query(None, description="Search by email or display name"),
    role: Optional[str] = Query(None, description="Filter by role (user, moderator, admin)"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get paginated list of users with filters:
    - **page**: Page number (starts from 1)
    - **limit**: Records per page (1-100)
    - **search**: Search in email and display name
    - **role**: Filter by role (user, moderator, admin)
    - **status**: Filter by status (active, inactive)
    
    **Requires admin role**
    """
    return await controller.get_users(
        page=page,
        limit=limit,
        search=search,
        role=role,
        status=status
    )


@router.get(
    "/stats",
    response_model=SuccessResponse[UserStatsResponse],
    summary="Get User Statistics",
    description="Get overall user statistics"
)
async def get_user_stats(
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get overall user statistics:
    - Total users
    - Active users
    - Verified users
    - Users by role
    
    **Requires admin role**
    """
    return await controller.get_user_stats()


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Get User Detail",
    description="Get detailed information about a specific user"
)
async def get_user_detail(
    user_id: str,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Get detailed information about a specific user by ID.
    
    **Requires admin role**
    """
    return await controller.get_user_detail(user_id)


@router.post(
    "",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Create New User",
    description="Create a new user account",
    status_code=201
)
async def create_user(
    user_data: CreateUserRequest,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Create a new user account with the following information:
    - **email**: Valid email address (unique)
    - **display_name**: User's display name (2-100 characters)
    - **password**: Password (minimum 6 characters)
    - **role**: User role (user, moderator, admin)
    
    Admin-created users are automatically verified.
    
    **Requires admin role**
    """
    return await controller.create_user(user_data)


@router.put(
    "/{user_id}",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Update User",
    description="Update user information"
)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Update user information. All fields are optional:
    - **display_name**: Update display name
    - **email**: Update email (must be unique)
    - **role**: Update role (user, moderator, admin)
    - **is_active**: Update active status
    
    **Requires admin role**
    """
    return await controller.update_user(user_id, user_data)


@router.patch(
    "/{user_id}/status",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Update User Status",
    description="Update user active/inactive status"
)
async def update_user_status(
    user_id: str,
    status_data: UpdateUserStatusRequest,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Update user active/inactive status.
    
    Setting is_active to False will effectively disable the user account.
    
    **Requires admin role**
    """
    return await controller.update_user_status(user_id, status_data)


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse,
    summary="Delete User",
    description="Delete a user account (soft delete)"
)
async def delete_user(
    user_id: str,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Delete a user account (soft delete).
    
    This sets the user's is_active status to False rather than permanently deleting the record.
    
    **Requires admin role**
    """
    return await controller.delete_user(user_id)


@router.post(
    "/{user_id}/resend-verification",
    response_model=SuccessResponse,
    summary="Resend Verification Email",
    description="Resend verification email to unverified user"
)
async def resend_verification_email(
    user_id: str,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Resend verification email to user.
    
    This endpoint will:
    - Check if user exists and is not verified
    - Generate new verification token
    - Send verification email
    
    **Requires admin role**
    """
    return await controller.resend_verification_email(user_id)


@router.get(
    "/health/check",
    response_model=SuccessResponse[dict],
    summary="User Management Service Health Check",
    description="Check if user management service is healthy"
)
async def user_management_health_check():
    """Health check endpoint for user management service"""
    return SuccessResponse(
        message="User management service is healthy",
        data={
            "status": "healthy",
            "service": "user_management",
            "version": "1.0.0"
        }
    )
