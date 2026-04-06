from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_active_user, get_token
from app.middleware.rate_limit import limiter
from app.modules.auth.dependencies import get_auth_service
from app.modules.users.models.user import User
from app.modules.auth.schemas.api import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    OAuth2TokenResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.modules.auth.service import AuthService
from app.shared.response import SuccessResponse

router = APIRouter(prefix="/auth")


@router.post(
    "/token",
    response_model=OAuth2TokenResponse,
    summary="OAuth2 login (Swagger Authorize)",
)
@limiter.limit("10/minute")
async def oauth2_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> OAuth2TokenResponse:
    """OAuth2 Password flow — dung cho Swagger UI. Frontend dung /signin."""
    result = await service.login(
        form_data=UserLogin(user_name=form_data.username, password=form_data.password),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return OAuth2TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


async def _build_user_response(user: User) -> UserResponse:
    """Build user response with eager-loaded relationships."""
    roles = []
    if user.user_roles:
        for ur in user.user_roles:
            if hasattr(ur, 'role') and ur.role:
                roles.append(ur.role.role_name)

    return UserResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_deleted=user.is_deleted,
        created_at=user.created_at,
        updated_at=user.updated_at,
        full_name=user.profile.full_name if user.profile else None,
        phone=user.profile.phone if user.profile else None,
        gender=user.profile.gender if user.profile else None,
        avatar_url=user.profile.avatar_url if user.profile else None,
        roles=roles,
    )


@router.post(
    "/signup",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    user = await service.register_user(
        user_data=user_data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    user_response = await _build_user_response(user)

    return SuccessResponse(
        message="Đăng ký tài khoản thành công",
        data=user_response,
    )


@router.post(
    "/signin",
    response_model=SuccessResponse[TokenResponse],
    summary="Login",
)
@limiter.limit("10/minute")
async def login_user(
    request: Request,
    credentials: UserLogin,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    result = await service.login(
        form_data=credentials,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    user = result["user"]
    user_response = await _build_user_response(user)

    return SuccessResponse(
        message="Đăng nhập thành công",
        data=TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=user_response,
        ),
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Refresh token",
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    result = await service.refresh_token(refresh_request.refresh_token)

    user_response = await _build_user_response(result["user"])

    return SuccessResponse(
        message="Làm mới token thành công",
        data=TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=user_response,
        ),
    )


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[PasswordResetResponse],
    summary="Request password reset",
)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    await service.initiate_password_reset(reset_request.email)
    return SuccessResponse(
        message="Yêu cầu đặt lại mật khẩu đang được xử lý",
        data=PasswordResetResponse(
            message="Nếu email tồn tại, "
            "bạn sẽ nhận được hướng dẫn đặt lại mật khẩu.",
            success=True,
        ),
    )


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse[PasswordResetResponse],
    summary="Confirm password reset",
)
@limiter.limit("5/minute")
async def confirm_password_reset(
    request: Request,
    reset_data: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    await service.reset_password(
        email=reset_data.email,
        token=reset_data.token,
        new_password=reset_data.new_password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return SuccessResponse(
        message="Đặt lại mật khẩu thành công",
        data=PasswordResetResponse(
            message="Mật khẩu đã được đặt lại. Hãy đăng nhập lại.",
            success=True,
        ),
    )


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get current user info",
)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    user = await service.get_user_by_id(current_user.user_id)
    if not user:
        from app.modules.auth.exceptions import UserNotFoundError

        raise UserNotFoundError(str(current_user.user_id))

    user_response = await _build_user_response(user)

    return SuccessResponse(
        message="Lấy thông tin người dùng thành công",
        data=user_response,
    )


@router.post(
    "/logout",
    response_model=SuccessResponse[dict],
    summary="Logout",
)
async def logout_user(
    request: Request,
    token: str = Depends(get_token),
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    result = await service.logout(
        token=token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return SuccessResponse(
        message="Đăng xuất thành công",
        data=result,
    )


@router.post(
    "/logout-all-devices",
    response_model=SuccessResponse[dict],
    summary="Logout from all devices",
)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    result = await service.revoke_all_user_tokens(current_user.user_id)

    return SuccessResponse(
        message="Đã đăng xuất khỏi tất cả thiết bị",
        data={
            "user_id": str(current_user.user_id),
            "old_version": result["old_version"],
            "new_version": result["new_version"],
            "message": "Tất cả token đã bị thu hồi",
        },
    )


@router.post(
    "/change-password",
    response_model=SuccessResponse[ChangePasswordResponse],
    summary="Change password",
)
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    await service.change_password(
        user_id=current_user.user_id,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    await service.revoke_all_user_tokens(current_user.user_id)

    return SuccessResponse(
        message="Mật khẩu đã được thay đổi. Tất cả thiết bị đã đăng xuất.",
        data=ChangePasswordResponse(
            message="Vui lòng đăng nhập lại với mật khẩu mới.",
            success=True,
        ),
    )


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Health check",
)
async def health_check() -> SuccessResponse:
    from datetime import datetime, timezone
    return SuccessResponse(
        message="Auth service đang hoạt động",
        data={
            "service": "auth",
            "status": "healthy",
            "features": {
                "user_registration": True,
                "user_authentication": True,
                "jwt_tokens": True,
                "email_verification": True,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
