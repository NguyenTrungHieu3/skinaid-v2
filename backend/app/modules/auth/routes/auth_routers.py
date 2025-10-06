from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
from pydantic import BaseModel
from datetime import datetime, timezone

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.modules.auth.models.user import User
from app.modules.auth.schemas.token import TokenResponse
from app.modules.auth.controllers.auth_controllers import AuthController
from app.api.v1.deps import get_db, get_current_active_user, get_token
from app.core.security import JWTHandler

jwt_handler = JWTHandler()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(db)
@router.post(
    "/signup",
    response_model=Union[SuccessResponse[UserResponse], ErrorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký user mới",
)
async def register_user(
    user_data: UserCreate,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.register_user(user_data)


@router.post(
    "/signin",
    response_model=Union[SuccessResponse[TokenResponse], ErrorResponse],
    summary="Đăng nhập",
)
async def login_user(
    credentials: UserLogin,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.login_user(credentials)

@router.post(
    "/verify-email",
    response_model=Union[SuccessResponse[EmailVerificationResponse], ErrorResponse],
    summary="Xác thực email (POST)",
)
async def verify_email_post(
    verification_data: EmailVerificationRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.verify_email(verification_data)

@router.get(
    "/verify-email",
    response_model=Union[SuccessResponse[EmailVerificationResponse], ErrorResponse],
    summary="Xác thực email qua link",
)
async def verify_email_get(
    email: str = Query(..., description="Email cần xác thực"),
    token: str = Query(..., description="Token xác thực email"),
    controller: AuthController = Depends(get_auth_controller),
):
    verification_data = EmailVerificationRequest(email=email, token=token)
    return await controller.verify_email(verification_data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Thông tin user hiện tại",
)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse(
        user_id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name or "",
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        full_name=current_user.profile.full_name if current_user.profile else None,
        phone=current_user.profile.phone if current_user.profile else None,
        avatar_url=current_user.profile.avatar_url if current_user.profile else None
    )


@router.post(
    "/password-reset/request",
    response_model=Union[SuccessResponse[dict], ErrorResponse],
    summary="Yêu cầu đặt lại mật khẩu",
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.request_password_reset(reset_request)


@router.post(
    "/password-reset/confirm",
    response_model=Union[SuccessResponse[dict], ErrorResponse],
    summary="Xác nhận đặt lại mật khẩu",
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.reset_password(reset_data)


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Kiểm tra tình trạng service",
)
async def health_check(controller: AuthController = Depends(get_auth_controller)):
    return await controller.health_check()


@router.post(
    "/refresh",
    response_model=Union[SuccessResponse[TokenResponse], ErrorResponse],
    summary="Làm mới token",
)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.refresh_token(refresh_request)


@router.post(
    "/logout",
    response_model=SuccessResponse[dict],
    summary="Đăng xuất",
)
async def logout_user(
    token: str = Depends(get_token),
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.logout_user(token)


@router.post(
    "/resend-verification",
    response_model=Union[SuccessResponse[dict], ErrorResponse],
    summary="Gửi lại email xác thực",
)
async def resend_verification_email(
    email_request: EmailVerificationRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.resend_verification_email(email_request.email)