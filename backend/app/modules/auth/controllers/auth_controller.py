import logging
from datetime import datetime, timezone
from typing import Union
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.schemas.user_schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
)
from app.modules.auth.schemas.token_schemas import TokenResponse
from app.modules.auth.services.auth_service import AuthService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.core.Security.jwt import jwt_handler
from app.core.tasks.token_family_service import (
    create_token_family,
    check_token_family_revoked,
    revoke_token_family,
    revoke_entire_chain,
)
from app.modules.auth.models.user import User

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)


class AuthController:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth_service: AuthService = AuthService(db)

    # =====================================================================
    # REGISTER
    # =====================================================================

    async def register_user(
        self,
        user_data: UserCreate,
    ) -> Union[SuccessResponse[UserResponse], ErrorResponse]:
        """Đăng ký user mới."""
        try:
            logger.info("[REGISTER] Starting registration for email: %s", user_data.email)

            user: User = await self.auth_service.create_user(user_data)

            user_response = UserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_deleted=getattr(user, "is_deleted", False),
                created_at=user.created_at,
                updated_at=user.updated_at,
                full_name=user.profile.full_name
                if getattr(user, "profile", None)
                else None,
                phone=user.profile.phone if getattr(user, "profile", None) else None,
                gender=user.profile.gender if getattr(user, "profile", None) else None,
                avatar_url=user.profile.avatar_url
                if getattr(user, "profile", None)
                else None,
            )

            logger.info("[REGISTER] Success: %s", user.user_id)

            return SuccessResponse(
                message=Message.USER_REGISTER_SUCCESS_MSG,
                data=user_response,
                status_code=status.HTTP_201_CREATED,
            )

        except AppBaseException as e:
            logger.error("[REGISTER] AppBaseException: %s", e.message)

            if e.error_code == ErrorCode.AUTH_EMAIL_EXISTS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"email": user_data.email},
                    status_code=status.HTTP_409_CONFLICT,
                )
            if e.error_code == ErrorCode.AUTH_PASSWORD_WEAK:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"requirements": Message.PASSWORD_REQUIREMENTS},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if e.error_code == ErrorCode.USER_INVALID_DATA:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"validation_error": str(e)},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.UNKNOWN_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:  # noqa: F841
            logger.error("[REGISTER] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================================
    # LOGIN (TOKEN FAMILY + VERSION)
    # =====================================================================

    async def login_user(
        self,
        credentials: UserLogin,
    ) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        """Đăng nhập và trả về access/refresh token kèm token_family."""
        try:
            logger.info(
                "[LOGIN] Attempting login for username: %s",
                credentials.user_name,
            )

            user = await self.auth_service.authenticate_user(
                credentials.user_name,
                credentials.password,
            )

            # Lấy token_version hiện tại
            token_version = await self.auth_service.get_user_token_version(
                user.user_id,
            )
            if token_version is None:
                token_version = 0

            # Tạo token pair
            tokens = jwt_handler.create_token_pair(
                subject=str(user.user_id),
                token_version=token_version,
            )

            # Lưu token family
            await create_token_family(
                db=self.db,
                user_id=str(user.user_id),
                refresh_jti=tokens["refresh_jti"],
                access_jti=tokens["access_jti"],
                refresh_exp=tokens["refresh_exp"],
            )

            user_response = UserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_deleted=getattr(user, "is_deleted", False),
                created_at=user.created_at,
                updated_at=user.updated_at,
                full_name=user.profile.full_name
                if getattr(user, "profile", None)
                else None,
                phone=user.profile.phone if getattr(user, "profile", None) else None,
                gender=user.profile.gender if getattr(user, "profile", None) else None,
                avatar_url=user.profile.avatar_url
                if getattr(user, "profile", None)
                else None,
            )

            token_response = TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                user=user_response,
            )

            logger.info("[LOGIN] Success: %s", user.user_id)

            return SuccessResponse(
                message=Message.USER_LOGIN_SUCCESS_MSG,
                data=token_response,
            )

        except AppBaseException as e:
            logger.error("[LOGIN] AppBaseException: %s", e.message)

            if e.error_code == ErrorCode.AUTH_INVALID_CREDENTIALS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"attempted_username": credentials.user_name},
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
            if e.error_code == ErrorCode.AUTH_ACCOUNT_INACTIVE:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"username": credentials.user_name},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            if e.error_code == ErrorCode.AUTH_VERIFICATION_REQUIRED:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={
                        "username": credentials.user_name,
                        "verification_required": True,
                    },
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.UNKNOWN_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:  # noqa: F841
            logger.error("[LOGIN] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================================
    # PASSWORD RESET
    # =====================================================================

    async def request_password_reset(
        self,
        reset_request: PasswordResetRequest,
    ) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        """Yêu cầu gửi email reset mật khẩu (ẩn sự tồn tại email)."""
        try:
            logger.info(
                "[PASSWORD_RESET_REQUEST] Email: %s",
                reset_request.email,
            )

            await self.auth_service.initiate_password_reset(reset_request.email)

            logger.info(
                "[PASSWORD_RESET_REQUEST] Request processed for: %s",
                reset_request.email,
            )

            return SuccessResponse(
                message=Message.PASSWORD_RESET_REQUEST_PROCESSING_MSG,
                data=PasswordResetResponse(
                    message=Message.PASSWORD_RESET_PROCESSED_MSG,
                    success=True,
                ),
            )

        except Exception as e:  
            logger.error(
                "[PASSWORD_RESET_REQUEST] Unexpected error",
                exc_info=True,
            )
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def reset_password(
        self,
        reset_data: PasswordResetConfirm,
    ) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        """Đặt lại mật khẩu bằng token reset."""
        try:
            logger.info(
                "[RESET_PASSWORD] Resetting password for: %s",
                reset_data.email,
            )

            success = await self.auth_service.reset_password(
                reset_data.email,
                reset_data.token,
                reset_data.new_password,
            )

            if success:
                logger.info(
                    "[RESET_PASSWORD] Success for: %s",
                    reset_data.email,
                )
                return SuccessResponse(
                    message=Message.PASSWORD_RESET_SUCCESS_MSG,
                    data=PasswordResetResponse(
                        message=Message.PASSWORD_RESET_SUCCESSFUL_MSG,
                        success=True,
                    ),
                )

            logger.warning(
                "[RESET_PASSWORD] Failed for: %s",
                reset_data.email,
            )
            return ErrorResponse(
                message=Message.AUTH_RESET_PASSWORD_FAILED_MSG,
                error_code=ErrorCode.PASSWORD_RESET_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except AppBaseException as e:
            logger.error("[RESET_PASSWORD] AppBaseException: %s", e.message)
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.PASSWORD_RESET_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:  # noqa: F841
            logger.error(
                "[RESET_PASSWORD] Unexpected error",
                exc_info=True,
            )
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================================
    # REFRESH TOKEN (ROTATION + REUSE DETECTION)
    # =====================================================================

    async def refresh_token(
        self,
        refresh_request,
    ) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        """
        Làm mới access token với rotation + reuse detection.

        Flow:
        1. Decode refresh token.
        2. Kiểm tra type + claims.
        3. Kiểm tra token_family bị revoke (reuse detection).
        4. Kiểm tra token_version so với DB.
        5. Revoke family cũ, tạo token_pair + family mới.
        """
        try:
            logger.info("[REFRESH_TOKEN] Refreshing token")

            # 1. Decode refresh token
            payload = jwt_handler.decode_token(
                refresh_request.refresh_token,
                verify_exp=True,
            )
            user_id = payload.get("sub")
            token_type = payload.get("type")
            token_version = payload.get("ver", 0)
            old_refresh_jti = payload.get("jti")

            # 2. Validate type + claims
            if token_type != "refresh":
                logger.warning("[REFRESH_TOKEN] Invalid token type")
                return ErrorResponse(
                    message=Message.AUTH_INVALID_TOKEN_TYPE_MSG,
                    error_code=ErrorCode.AUTH_INVALID_TOKEN_TYPE,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            if not user_id or not old_refresh_jti:
                logger.warning(
                    "[REFRESH_TOKEN] Invalid token - missing claims",
                )
                return ErrorResponse(
                    message=Message.AUTH_INVALID_TOKEN_MSG,
                    error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # 3. Reuse detection
            is_revoked = await check_token_family_revoked(self.db, old_refresh_jti)
            if is_revoked:
                logger.error(
                    "[REFRESH_TOKEN] REUSE DETECTED for user %s, jti: %s. Revoking entire chain.",
                    user_id,
                    old_refresh_jti,
                )
                await revoke_entire_chain(self.db, old_refresh_jti)
                return ErrorResponse(
                    message=Message.AUTH_TOKEN_REUSE_DETECTED_MSG,
                    error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # 4. Check token_version vs DB
            current_version = await self.auth_service.get_user_token_version(
                uuid.UUID(user_id),
            )
            if current_version is None:
                return ErrorResponse(
                    message=Message.AUTH_USER_NOT_FOUND_MSG,
                    error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            if token_version < current_version:
                logger.warning(
                    "[REFRESH_TOKEN] Old token version: %s < %s",
                    token_version,
                    current_version,
                )
                return ErrorResponse(
                    message=Message.AUTH_TOKEN_REVOKED_MSG,
                    error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # 5. Revoke old family + tạo mới
            await revoke_token_family(self.db, old_refresh_jti)

            user = await self.auth_service.get_user_by_id(uuid.UUID(user_id))
            if not user:
                logger.warning(
                    "[REFRESH_TOKEN] User not found: %s",
                    user_id,
                )
                return ErrorResponse(
                    message=Message.AUTH_USER_NOT_FOUND_MSG,
                    error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            new_tokens = jwt_handler.create_token_pair(
                subject=user_id,
                token_version=current_version,
            )

            await create_token_family(
                db=self.db,
                user_id=user_id,
                refresh_jti=new_tokens["refresh_jti"],
                access_jti=new_tokens["access_jti"],
                refresh_exp=new_tokens["refresh_exp"],
                parent_jti=old_refresh_jti,
            )

            user_response = UserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_deleted=getattr(user, "is_deleted", False),
                created_at=user.created_at,
                updated_at=user.updated_at,
                full_name=user.profile.full_name
                if getattr(user, "profile", None)
                else None,
                phone=user.profile.phone if getattr(user, "profile", None) else None,
                gender=user.profile.gender if getattr(user, "profile", None) else None,
                avatar_url=user.profile.avatar_url
                if getattr(user, "profile", None)
                else None,
            )

            token_response = TokenResponse(
                access_token=new_tokens["access_token"],
                refresh_token=new_tokens["refresh_token"],
                user=user_response,
            )

            logger.info("[REFRESH_TOKEN] Success: %s", user_id)

            return SuccessResponse(
                message=Message.TOKEN_REFRESH_SUCCESS_MSG,
                data=token_response,
            )

        except HTTPException:
            raise

        except Exception as e:  # noqa: F841
            logger.error(
                "[REFRESH_TOKEN] Unexpected error",
                exc_info=True,
            )
            return ErrorResponse(
                message=Message.AUTH_INVALID_REFRESH_TOKEN_MSG,
                error_code=ErrorCode.INVALID_REFRESH_TOKEN,
                error_details={"error": str(e)},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

    # =====================================================================
    # LOGOUT (REVOKE TOKEN FAMILY)
    # =====================================================================

    async def logout_user(self, token: str) -> SuccessResponse[dict]:
        """
        Đăng xuất 1 phiên:
        - Decode token lấy jti.
        - Revoke token_family tương ứng.
        - Idempotent: luôn trả success an toàn.
        """
        try:
            logger.info("[LOGOUT] Processing logout")

            payload = jwt_handler.decode_token(token, verify_exp=False)
            jti = payload.get("jti")

            if not jti:
                logger.warning("[LOGOUT] Token missing JTI")
                return SuccessResponse(
                    message=Message.USER_LOGOUT_SUCCESS_MSG,
                    data={
                        "logout_time": datetime.now(timezone.utc).isoformat(),
                        "message": Message.SESSION_TERMINATED_MSG,
                    },
                )

            revoked_count = await revoke_token_family(self.db, jti)

            logger.info(
                "[LOGOUT] Revoked %s tokens in family",
                revoked_count,
            )

            return SuccessResponse(
                message=Message.USER_LOGOUT_SUCCESS_MSG,
                data={
                    "logout_time": datetime.now(timezone.utc).isoformat(),
                    "message": (
                        f"Logged out successfully. {revoked_count} token(s) revoked."
                    ),
                    "tokens_revoked": revoked_count,
                },
            )

        except Exception as e:  # noqa: Fашь
            logger.warning(
                "[LOGOUT] Error during logout, returning generic success",
                exc_info=True,
            )
            return SuccessResponse(
                message=Message.USER_LOGOUT_SUCCESS_MSG,
                data={
                    "logout_time": datetime.now(timezone.utc).isoformat(),
                    "message": Message.SESSION_TERMINATED_MSG,
                },
            )

    # =====================================================================
    # LOGOUT ALL DEVICES (TOKEN VERSION++)
    # =====================================================================

    async def logout_all_devices(
        self,
        current_user: User,
    ) -> Union[SuccessResponse[dict], ErrorResponse]:
        """
        Đăng xuất khỏi tất cả thiết bị:
        - Gọi AuthService.revoke_all_user_tokens (increment token_version).
        """
        try:
            logger.info(
                "[LOGOUT_ALL] User: %s",
                current_user.user_id,
            )

            result = await self.auth_service.revoke_all_user_tokens(
                current_user.user_id,
            )

            if not result.get("success"):
                return ErrorResponse(
                    message=result.get("message", Message.AUTH_USER_NOT_FOUND_MSG),
                    error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            logger.info(
                "[LOGOUT_ALL] Success: %s",
                current_user.user_id,
            )

            return SuccessResponse(
                message="Logged out from all devices successfully",
                data={
                    "user_id": str(current_user.user_id),
                    "old_version": result["old_version"],
                    "new_version": result["new_version"],
                    "message": (
                        "All tokens have been revoked. Please login again."
                    ),
                },
            )

        except Exception as e:  # noqa: F841
            logger.error("[LOGOUT_ALL] Error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =====================================================================
    # HEALTH CHECK
    # =====================================================================

    async def health_check(self) -> SuccessResponse[dict]:
        """Health check cho auth service."""
        logger.debug("[HEALTH] Checking auth service...")
        return SuccessResponse(
            message=Message.AUTH_HEALTH_CHECK_MSG,
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

    # =====================================================================
    # CHANGE PASSWORD (AUTO LOGOUT ALL DEVICES)
    # =====================================================================

    async def change_password(
        self,
        current_user: User,
        password_data: ChangePasswordRequest,
    ) -> Union[SuccessResponse[ChangePasswordResponse], ErrorResponse]:
        """Đổi mật khẩu và tự động revoke toàn bộ tokens (logout all devices)."""
        try:
            logger.info(
                "[CHANGE_PASSWORD] User: %s",
                current_user.user_id,
            )

            success = await self.auth_service.change_password(
                user_id=current_user.user_id,
                old_password=password_data.old_password,
                new_password=password_data.new_password,
            )

            if not success:
                logger.warning(
                    "[CHANGE_PASSWORD] Failed: %s",
                    current_user.user_id,
                )
                return ErrorResponse(
                    message=Message.AUTH_CHANGE_PASSWORD_FAILED_MSG,
                    error_code=ErrorCode.PASSWORD_CHANGE_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            revoke_result = await self.auth_service.revoke_all_user_tokens(
                current_user.user_id,
            )

            logger.info(
                "[CHANGE_PASSWORD] Success + All tokens revoked: %s, %s -> %s",
                current_user.user_id,
                revoke_result.get("old_version"),
                revoke_result.get("new_version"),
            )

            return SuccessResponse(
                message="Password changed successfully. All devices have been logged out.",
                data=ChangePasswordResponse(
                    message="Password changed. Please login again on all devices.",
                    success=True,
                ),
            )

        except AppBaseException as e:
            logger.error("[CHANGE_PASSWORD] AppBaseException: %s", e.message)

            if e.error_code == ErrorCode.AUTH_PASSWORD_WEAK:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"requirements": Message.PASSWORD_REQUIREMENTS},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if e.error_code == ErrorCode.AUTH_INVALID_CREDENTIALS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"field": "old_password"},
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.PASSWORD_CHANGE_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:  
            logger.error(
                "[CHANGE_PASSWORD] Unexpected error",
                exc_info=True,
            )
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
