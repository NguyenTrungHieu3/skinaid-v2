import logging
from datetime import datetime, timezone
from typing import Union, Optional, List
import uuid

from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.schemas.user_schemas import (
    UserCreate, UserLogin, UserResponse, PasswordResetRequest,
    PasswordResetConfirm, PasswordResetResponse, ChangePasswordRequest, ChangePasswordResponse
)
from app.modules.auth.schemas.token_schemas import TokenResponse
from app.modules.auth.services.auth_service import AuthService
from app.core.Security.jwt import jwt_handler
from app.modules.auth.services.token_family_service import TokenFamilyService
from app.modules.auth.models.user import User
from app.utils.constants import error_codes as ErrorCode, messages as Message

logger = logging.getLogger(__name__)


class AuthController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth_service = AuthService(db)

    def _build_user_response(self, user: User, roles: Optional[List[str]] = None) -> UserResponse:
        return UserResponse(
            user_id=user.user_id, user_name=user.user_name, email=user.email,
            is_active=user.is_active, is_verified=user.is_verified,
            is_deleted=getattr(user, "is_deleted", False),
            created_at=user.created_at, updated_at=user.updated_at,
            full_name=user.profile.full_name if user.profile else None,
            phone=user.profile.phone if user.profile else None,
            gender=user.profile.gender if user.profile else None,
            avatar_url=user.profile.avatar_url if user.profile else None,
            roles=roles if roles is not None else []
        )

    async def register_user(self, user_data: UserCreate) -> Union[SuccessResponse[UserResponse], ErrorResponse]:
        try:
            logger.info("[REGISTER] Email: %s", user_data.email)
            user = await self.auth_service.create_user(user_data)
            logger.info("[REGISTER] Success: %s", user.user_id)
            return SuccessResponse(
                message=Message.USER_REGISTER_SUCCESS_MSG,
                data=self._build_user_response(user),
                status_code=status.HTTP_201_CREATED
            )
        except HTTPException as e:
            logger.warning("[REGISTER] Validation error: %s", e.detail)
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.USER_INVALID_DATA,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error("[REGISTER] Error: %s", e, exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG, error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def login_user(self, credentials: UserLogin) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        try:
            logger.info("[LOGIN] Username: %s", credentials.user_name)
            user = await self.auth_service.authenticate_user(credentials.user_name, credentials.password)
            
            token_version = await self.auth_service.get_user_token_version(user.user_id) or 0
            tokens = jwt_handler.create_token_pair(subject=str(user.user_id), token_version=token_version)
            
            await TokenFamilyService.create_token_family(
                db=self.db, user_id=str(user.user_id),
                refresh_jti=tokens["refresh_jti"], access_jti=tokens["access_jti"],
                refresh_exp=tokens["refresh_exp"]
            )
            
            user_roles = [ur.role.role_name for ur in user.user_roles if ur.role] if user.user_roles else []
            logger.info("[LOGIN] Success: %s", user.user_id)
            
            return SuccessResponse(
                message=Message.USER_LOGIN_SUCCESS_MSG,
                data=TokenResponse(
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                    user=self._build_user_response(user, user_roles)
                )
            )
        except HTTPException as e:
            logger.warning("[LOGIN] Auth failed: %s", e.detail)
            return ErrorResponse(
                message=e.detail, error_code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                error_details={"error": e.detail}, status_code=e.status_code
            )
        except Exception as e:
            logger.error("[LOGIN] Error: %s", e, exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG, error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def request_password_reset(self, reset_request: PasswordResetRequest) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        try:
            logger.info("[PASSWORD_RESET_REQUEST] Email: %s", reset_request.email)
            await self.auth_service.initiate_password_reset(reset_request.email)
            return SuccessResponse(
                message=Message.PASSWORD_RESET_REQUEST_PROCESSING_MSG,
                data=PasswordResetResponse(message=Message.PASSWORD_RESET_PROCESSED_MSG, success=True)
            )
        except Exception as e:
            logger.error("[PASSWORD_RESET_REQUEST] Error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG, error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def reset_password(self, reset_data: PasswordResetConfirm) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        try:
            logger.info("[RESET_PASSWORD] Email: %s", reset_data.email)
            success = await self.auth_service.reset_password(reset_data.email, reset_data.token, reset_data.new_password)
            
            if success:
                logger.info("[RESET_PASSWORD] Success: %s", reset_data.email)
                return SuccessResponse(
                    message=Message.PASSWORD_RESET_SUCCESS_MSG,
                    data=PasswordResetResponse(message=Message.PASSWORD_RESET_SUCCESSFUL_MSG, success=True)
                )
            
            logger.warning("[RESET_PASSWORD] Failed: %s", reset_data.email)
            return ErrorResponse(
                message=Message.AUTH_RESET_PASSWORD_FAILED_MSG,
                error_code=ErrorCode.PASSWORD_RESET_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except HTTPException as e:
            logger.warning("[RESET_PASSWORD] Validation error: %s", e.detail)
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.PASSWORD_RESET_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error("[RESET_PASSWORD] Error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG, error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def refresh_token(self, refresh_request) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        try:
            logger.info("[REFRESH_TOKEN] Processing")
            payload = jwt_handler.decode_token(refresh_request.refresh_token, verify_exp=True)
            user_id, token_type, token_version, old_jti = (
                payload.get("sub"), payload.get("type"), payload.get("ver", 0), payload.get("jti")
            )
            
            if token_type != "refresh" or not user_id or not old_jti:
                return ErrorResponse(
                    message=Message.AUTH_INVALID_TOKEN_MSG, error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            if await TokenFamilyService.check_token_family_revoked(self.db, old_jti):
                logger.error("[REFRESH_TOKEN] REUSE DETECTED user %s jti: %s", user_id, old_jti)
                await TokenFamilyService.revoke_entire_chain(self.db, old_jti)
                return ErrorResponse(
                    message=Message.AUTH_TOKEN_REUSE_DETECTED_MSG, error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            current_version = await self.auth_service.get_user_token_version(uuid.UUID(user_id))
            if current_version is None or token_version < current_version:
                return ErrorResponse(
                    message=Message.AUTH_TOKEN_REVOKED_MSG, error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            await TokenFamilyService.revoke_token_family(self.db, old_jti)
            
            user = await self.auth_service.get_user_by_id(uuid.UUID(user_id))
            if not user:
                return ErrorResponse(
                    message=Message.AUTH_USER_NOT_FOUND_MSG, error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            new_tokens = jwt_handler.create_token_pair(subject=user_id, token_version=current_version)
            await TokenFamilyService.create_token_family(
                db=self.db, user_id=user_id, refresh_jti=new_tokens["refresh_jti"],
                access_jti=new_tokens["access_jti"], refresh_exp=new_tokens["refresh_exp"], parent_jti=old_jti
            )
            
            logger.info("[REFRESH_TOKEN] Success: %s", user_id)
            return SuccessResponse(
                message=Message.TOKEN_REFRESH_SUCCESS_MSG,
                data=TokenResponse(
                    access_token=new_tokens["access_token"],
                    refresh_token=new_tokens["refresh_token"],
                    user=self._build_user_response(user)
                )
            )
        except Exception as e:
            logger.error("[REFRESH_TOKEN] Error", exc_info=True)
            return ErrorResponse(
                message=Message.AUTH_INVALID_REFRESH_TOKEN_MSG, error_code=ErrorCode.INVALID_REFRESH_TOKEN,
                error_details={"error": str(e)}, status_code=status.HTTP_401_UNAUTHORIZED
            )

    async def logout_user(self, token: str) -> SuccessResponse[dict]:
        try:
            logger.info("[LOGOUT] Processing")
            payload = jwt_handler.decode_token(token, verify_exp=False)
            jti = payload.get("jti")
            
            if not jti:
                return SuccessResponse(
                    message=Message.USER_LOGOUT_SUCCESS_MSG,
                    data={"logout_time": datetime.now(timezone.utc).isoformat(), "message": Message.SESSION_TERMINATED_MSG}
                )
            
            revoked_count = await TokenFamilyService.revoke_token_family(self.db, jti)
            logger.info("[LOGOUT] Revoked %s tokens", revoked_count)
            
            return SuccessResponse(
                message=Message.USER_LOGOUT_SUCCESS_MSG,
                data={
                    "logout_time": datetime.now(timezone.utc).isoformat(),
                    "message": Message.LOGOUT_SUCCESS_TOKENS_REVOKED_MSG.format(revoked_count=revoked_count),
                    "tokens_revoked": revoked_count
                }
            )
        except Exception as e:
            logger.warning("[LOGOUT] Error, returning success", exc_info=True)
            return SuccessResponse(
                message=Message.USER_LOGOUT_SUCCESS_MSG,
                data={"logout_time": datetime.now(timezone.utc).isoformat(), "message": Message.SESSION_TERMINATED_MSG}
            )

    async def logout_all_devices(self, current_user: User) -> Union[SuccessResponse[dict], ErrorResponse]:
        try:
            logger.info("[LOGOUT_ALL] User: %s", current_user.user_id)
            result = await self.auth_service.revoke_all_user_tokens(current_user.user_id)
            
            if not result.get("success"):
                return ErrorResponse(
                    message=result.get("message", Message.AUTH_USER_NOT_FOUND_MSG),
                    error_code=ErrorCode.USER_NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND
                )
            
            logger.info("[LOGOUT_ALL] Success: %s", current_user.user_id)
            return SuccessResponse(
                message=Message.LOGOUT_ALL_DEVICES_SUCCESS_MSG,
                data={
                    "user_id": str(current_user.user_id),
                    "old_version": result["old_version"], "new_version": result["new_version"],
                    "message": Message.ALL_TOKENS_REVOKED_MSG
                }
            )
        except Exception as e:
            logger.error("[LOGOUT_ALL] Error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG, error_code=ErrorCode.INTERNAL_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def health_check(self) -> SuccessResponse[dict]:
        return SuccessResponse(
            message=Message.AUTH_HEALTH_CHECK_MSG,
            data={
                "service": "auth", "status": "healthy",
                "features": {"user_registration": True, "user_authentication": True, "jwt_tokens": True, "email_verification": True},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    async def change_password(self, current_user: User, password_data: ChangePasswordRequest) -> Union[SuccessResponse[ChangePasswordResponse], ErrorResponse]:
        try:
            logger.info("[CHANGE_PASSWORD] User: %s", current_user.user_id)
            success = await self.auth_service.change_password(
                user_id=current_user.user_id, old_password=password_data.old_password, new_password=password_data.new_password
            )
            
            if not success:
                logger.warning("[CHANGE_PASSWORD] Failed: %s", current_user.user_id)
                return ErrorResponse(
                    message=Message.AUTH_CHANGE_PASSWORD_FAILED_MSG,
                    error_code=ErrorCode.PASSWORD_CHANGE_ERROR, status_code=status.HTTP_400_BAD_REQUEST
                )
            
            await self.auth_service.revoke_all_user_tokens(current_user.user_id)
            logger.info("[CHANGE_PASSWORD] Success + all tokens revoked: %s", current_user.user_id)
            
            return SuccessResponse(
                message=Message.PASSWORD_CHANGED_ALL_DEVICES_LOGOUT_MSG,
                data=ChangePasswordResponse(message=Message.PASSWORD_CHANGED_LOGIN_AGAIN_MSG, success=True)
            )
        except Exception as e:
            logger.error("[CHANGE_PASSWORD] Error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG, error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
