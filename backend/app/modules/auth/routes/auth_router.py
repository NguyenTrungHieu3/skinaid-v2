from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
from pydantic import BaseModel
from datetime import datetime, timezone

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.schemas.user_schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    # EmailVerificationRequest,
    # EmailVerificationResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    ChangePasswordResponse
)
from app.modules.auth.models.user import User
from app.modules.auth.schemas.token_schemas import TokenResponse
from app.modules.auth.controllers.auth_controller import AuthController
from app.api.v1.deps import get_db, get_current_active_user, get_token
from app.core.Security.jwt import JWTHandler

jwt_handler = JWTHandler()

def handle_controller_response(result):
    if isinstance(result, ErrorResponse):
        return JSONResponse(
            status_code=result.status_code,
            content=jsonable_encoder(result)
        )
    return jsonable_encoder(result)

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
    """Đăng ký tài khoản mới. Sau khi đăng ký sẽ gửi email xác thực."""
    return handle_controller_response(await controller.register_user(user_data))

@router.post(
    "/signin",
    response_model=Union[SuccessResponse[TokenResponse], ErrorResponse],
    summary="Đăng nhập",
)
async def login_user(
    credentials: UserLogin,
    controller: AuthController = Depends(get_auth_controller),
):
    """Đăng nhập hệ thống và trả về token xác thực."""
    return handle_controller_response(await controller.login_user(credentials))

@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Thông tin user hiện tại",
)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Lấy thông tin cá nhân của user hiện tại."""
    user_response = UserResponse(
        user_id=current_user.user_id,
        user_name=current_user.user_name,
        email=current_user.email,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_deleted=current_user.is_deleted,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        full_name=current_user.profile.full_name if current_user.profile else None,
        phone=current_user.profile.phone if current_user.profile else None,
        gender=current_user.profile.gender if current_user.profile else None,
        avatar_url=current_user.profile.avatar_url if current_user.profile else None
    )

    return SuccessResponse(
        message="Lấy thông tin người dùng thành công",
        data=user_response
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
    """Gửi yêu cầu đặt lại mật khẩu qua email."""
    return handle_controller_response(await controller.request_password_reset(reset_request))


@router.post(
    "/password-reset/confirm",
    response_model=Union[SuccessResponse[dict], ErrorResponse],
    summary="Xác nhận đặt lại mật khẩu",
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    controller: AuthController = Depends(get_auth_controller),
):
    """Xác nhận đặt lại mật khẩu với token từ email."""
    return handle_controller_response(await controller.reset_password(reset_data))


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Kiểm tra tình trạng service",
)
async def health_check(controller: AuthController = Depends(get_auth_controller)):
    """Kiểm tra trạng thái hoạt động của service."""
    return handle_controller_response(await controller.health_check())


@router.post(
    "/refresh",
    response_model=Union[SuccessResponse[TokenResponse], ErrorResponse],
    summary="Làm mới token",
)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    """Làm mới access token bằng refresh token."""
    return handle_controller_response(await controller.refresh_token(refresh_request))


@router.post(
    "/logout",
    response_model=SuccessResponse[dict],
    summary="Đăng xuất",
)
async def logout_user(
    token: str = Depends(get_token),
    controller: AuthController = Depends(get_auth_controller),
):
    """Đăng xuất khỏi hệ thống và vô hiệu hóa token."""
    return handle_controller_response(await controller.logout_user(token))

@router.post(
    "/logout-all-devices",
    response_model=Union[SuccessResponse[dict], ErrorResponse],
    summary="Đăng xuất khỏi tất cả thiết bị",
)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    controller: AuthController = Depends(get_auth_controller),
):
    """
    Đăng xuất khỏi TẤT CẢ thiết bị.
    """
    return handle_controller_response(await controller.logout_all_devices(current_user))

@router.post(
    "/change-password", 
    response_model= Union[SuccessResponse[ChangePasswordResponse], ErrorResponse],
    summary="Thay đổi mật khẩu (auto logout all devices)"
)
async def change_password(
    password_data: ChangePasswordRequest,
    controller: AuthController = Depends(get_auth_controller),
    current_user: User = Depends(get_current_active_user)
):
    """Thay đổi mật khẩu tài khoản (đã đăng nhập)."""
    return handle_controller_response(await controller.change_password(current_user, password_data))

# ============= Email Verification Endpoints =============
# @router.post(
#     "/verify-email",
#     response_model=Union[SuccessResponse[EmailVerificationResponse], ErrorResponse],
#     summary="Xác thực email (POST)",
# )
# async def verify_email_post(
#     verification_data: EmailVerificationRequest,
#     controller: AuthController = Depends(get_auth_controller),
# ):
#     """Xác thực email thông qua mã token."""
#     return await controller.verify_email(verification_data)

# @router.get(
#     "/verify-email",
#     response_model=Union[SuccessResponse[EmailVerificationResponse], ErrorResponse],
#     summary="Xác thực email qua link",
# )
# async def verify_email_get(
#     email: str = Query(..., description="Email cần xác thực"),
#     token: str = Query(..., description="Token xác thực email"),
#     controller: AuthController = Depends(get_auth_controller),
# ):
#     """Xác thực email qua liên kết (GET request)."""
#     verification_data = EmailVerificationRequest(email=email, token=token)
#     return await controller.verify_email(verification_data)

# @router.post(
#     "/resend-verification",
#     response_model=Union[SuccessResponse[dict], ErrorResponse],
#     summary="Gửi lại email xác thực",
# )
# async def resend_verification_email(
#     email_request: PasswordResetRequest,
#     controller: AuthController = Depends(get_auth_controller),
# ):
#     """Gửi lại email xác thực tài khoản."""
#     return await controller.resend_verification_email(email_request.email)
# ============= Email Verification Endpoints =============