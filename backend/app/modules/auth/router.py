"""
Auth Router — Route → Service (no controller layer).

Router chỉ parse request, gọi service, build response.
Exception handling được global handler xử lý (shared/exceptions/handler.py).
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.Security.jwt import JWTHandler
from app.core.dependencies import get_current_active_user, get_db, get_token
from app.modules.audit.services.audit_service import AuditService
from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.models.user import User
from app.modules.auth.schemas.api import (
    ChangePasswordRequest,
    ChangePasswordResponse,
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

logger = logging.getLogger(__name__)

jwt_handler = JWTHandler()

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Helpers ───────────────────────────────────────────────


def _build_user_response(user: User) -> UserResponse:
    """Chuyển đổi User entity → UserResponse schema."""
    roles = (
        [ur.role.role_name for ur in user.user_roles if ur.role]
        if user.user_roles
        else []
    )

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


async def _audit(
    db: AsyncSession,
    request: Request,
    *,
    action: str,
    success: bool,
    user_id: uuid.UUID | str | None = None,
    resource_id: str | None = None,
    error_message: str | None = None,
    details: dict | None = None,
) -> None:
    """Audit log helper — fire-and-forget trong try/except."""
    try:
        audit_service = AuditService(db)
        await audit_service.log_event(
            action=action,
            user_id=user_id,
            success=success,
            resource_type="user",
            resource_id=resource_id or (str(user_id) if user_id else None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            error_message=error_message,
            details=details,
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", str(e))


# ══════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS
# ══════════════════════════════════════════════════════════


@router.post(
    "/signup",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký user mới",
)
async def register_user(
    request: Request,
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Đăng ký tài khoản mới. Sau khi đăng ký sẽ gửi email xác thực."""
    user = await service.register_user(user_data)
    user_response = _build_user_response(user)

    await _audit(
        db,
        request,
        action="register",
        success=True,
        user_id=user.user_id,
        details={"email": user_data.email, "user_name": user_data.user_name},
    )

    return SuccessResponse(
        message="Đăng ký tài khoản thành công",
        data=user_response,
    )


@router.post(
    "/signin",
    response_model=SuccessResponse[TokenResponse],
    summary="Đăng nhập",
)
async def login_user(
    request: Request,
    credentials: UserLogin,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Đăng nhập hệ thống và trả về token xác thực."""
    result = await service.login(credentials)
    user = result["user"]

    await _audit(
        db,
        request,
        action="login",
        success=True,
        user_id=user.user_id,
        details={"user_name": credentials.user_name},
    )

    return SuccessResponse(
        message="Đăng nhập thành công",
        data=TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=_build_user_response(user),
        ),
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Làm mới token",
)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """Làm mới access token bằng refresh token."""
    # Delegate logic to service
    result = await service.refresh_token(refresh_request.refresh_token)

    return SuccessResponse(
        message="Làm mới token thành công",
        data=TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=_build_user_response(result["user"]),
        ),
    )


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[PasswordResetResponse],
    summary="Yêu cầu đặt lại mật khẩu",
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """Gửi yêu cầu đặt lại mật khẩu qua email."""
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
    summary="Xác nhận đặt lại mật khẩu",
)
async def confirm_password_reset(
    request: Request,
    reset_data: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Xác nhận đặt lại mật khẩu với token từ email."""
    await service.reset_password(
        reset_data.email, reset_data.token, reset_data.new_password
    )

    await _audit(
        db,
        request,
        action="password_reset",
        success=True,
        details={"email": reset_data.email},
    )

    return SuccessResponse(
        message="Đặt lại mật khẩu thành công",
        data=PasswordResetResponse(
            message="Mật khẩu đã được đặt lại. Hãy đăng nhập lại.",
            success=True,
        ),
    )


# ══════════════════════════════════════════════════════════
# AUTHENTICATED ENDPOINTS
# ══════════════════════════════════════════════════════════


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Thông tin user hiện tại",
)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """Lấy thông tin cá nhân của user hiện tại."""
    user = await service.get_user_by_id(current_user.user_id)
    # user guaranteed to exist if current_user exists, but checking strict
    if not user:
        from app.modules.auth.exceptions import UserNotFoundError

        raise UserNotFoundError(str(current_user.user_id))

    return SuccessResponse(
        message="Lấy thông tin người dùng thành công",
        data=_build_user_response(user),
    )


@router.post(
    "/logout",
    response_model=SuccessResponse[dict],
    summary="Đăng xuất",
)
async def logout_user(
    request: Request,
    token: str = Depends(get_token),
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Đăng xuất khỏi hệ thống và vô hiệu hóa token."""
    now_iso = datetime.now(timezone.utc).isoformat()
    revoked_count = 0
    user_id = None

    try:
        # We decode just to get JTI and user_id for logging/revocation
        # Valid signature needed? verify_exp=False covers expired tokens on logout
        payload = jwt_handler.decode_token(token, verify_exp=False)
        jti = payload.get("jti")
        user_id = payload.get("sub")

        if jti:
            revoked_count = await service.revoke_token_family(jti)
    except Exception:
        # Token invalid — still return success
        pass

    await _audit(
        db,
        request,
        action="logout",
        success=True,
        user_id=user_id,
    )

    return SuccessResponse(
        message="Đăng xuất thành công",
        data={
            "logout_time": now_iso,
            "tokens_revoked": revoked_count,
            "message": f"Đã thu hồi {revoked_count} token"
            if revoked_count
            else "Phiên đã kết thúc",
        },
    )


@router.post(
    "/logout-all-devices",
    response_model=SuccessResponse[dict],
    summary="Đăng xuất khỏi tất cả thiết bị",
)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
    """Đăng xuất khỏi TẤT CẢ thiết bị."""
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
    summary="Thay đổi mật khẩu (auto logout all devices)",
)
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Thay đổi mật khẩu tài khoản (đã đăng nhập)."""
    await service.change_password(
        user_id=current_user.user_id,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
    )

    # Revoke all tokens sau khi đổi password
    await service.revoke_all_user_tokens(current_user.user_id)

    await _audit(
        db,
        request,
        action="change_password",
        success=True,
        user_id=current_user.user_id,
    )

    return SuccessResponse(
        message="Mật khẩu đã được thay đổi. Tất cả thiết bị đã đăng xuất.",
        data=ChangePasswordResponse(
            message="Vui lòng đăng nhập lại với mật khẩu mới.",
            success=True,
        ),
    )


# ══════════════════════════════════════════════════════════
# UTILITY
# ══════════════════════════════════════════════════════════


@router.get(
    "/health",
    response_model=SuccessResponse[dict],
    summary="Kiểm tra tình trạng service",
)
async def health_check() -> SuccessResponse:
    """Kiểm tra trạng thái hoạt động của service."""
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
