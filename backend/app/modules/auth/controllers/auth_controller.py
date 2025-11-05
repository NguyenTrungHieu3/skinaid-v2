from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
from datetime import datetime, timezone
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.schemas.user_schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse,
    ChangePasswordRequest,
    ChangePasswordResponse
)
from app.modules.auth.schemas.token_schemas import TokenResponse
from app.modules.auth.services.auth_service import AuthService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.core.Security.jwt import JWTHandler, blacklist_token
from app.modules.auth.models.user import User
from fastapi import HTTPException, status

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)
jwt_handler = JWTHandler()


class AuthController:

    def __init__(self, db: AsyncSession) -> None:
        self.auth_service: AuthService = AuthService(db)
    
    async def register_user(
        self,
        user_data: UserCreate
    ) -> Union[SuccessResponse[UserResponse], ErrorResponse]:
        """Register a new user."""
        try:
            logger.info(f"[REGISTER] Starting registration for email: {user_data.email}")
            
            user: User = await self.auth_service.create_user(user_data)
            
            user_response: UserResponse = UserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                full_name=user.profile.full_name if user.profile else None,
                phone=user.profile.phone if user.profile else None,
                gender=user.profile.gender if user.profile else None,
                avatar_url=user.profile.avatar_url if user.profile else None
            )

            logger.info(f"[REGISTER] Success: {user.user_id}")
            
            return SuccessResponse(
                message=Message.USER_REGISTER_SUCCESS_MSG,
                data=user_response,
                status_code=status.HTTP_201_CREATED
            )

        except AppBaseException as e:
            logger.error(f"[REGISTER] AppBaseException: {e.message}")
            
            if e.error_code == ErrorCode.AUTH_EMAIL_EXISTS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"email": user_data.email},
                    status_code=status.HTTP_409_CONFLICT
                )
            elif e.error_code == ErrorCode.AUTH_PASSWORD_WEAK:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"requirements": Message.PASSWORD_REQUIREMENTS},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            elif e.error_code == ErrorCode.USER_INVALID_DATA:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"validation_error": str(e)},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or ErrorCode.UNKNOWN_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"[REGISTER] Unexpected error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def login_user(
        self,
        credentials: UserLogin
    ) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        """Login user and return tokens."""
        try:
            logger.info(f"[LOGIN] Attempting login for username: {credentials.user_name}")
            
            user = await self.auth_service.authenticate_user(
                credentials.user_name,
                credentials.password
            )

            access_token = jwt_handler.create_access_token(subject=str(user.user_id))
            refresh_token = jwt_handler.create_refresh_token(subject=str(user.user_id))

            user_response = UserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                full_name=user.profile.full_name if user.profile else None,
                phone=user.profile.phone if user.profile else None,
                gender=user.profile.gender if user.profile else None,
                avatar_url=user.profile.avatar_url if user.profile else None
            )

            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_response
            )

            logger.info(f"[LOGIN] Success: {user.user_id}")
            
            return SuccessResponse(
                message=Message.USER_LOGIN_SUCCESS_MSG,
                data=token_response
            )

        except AppBaseException as e:
            logger.error(f"[LOGIN] AppBaseException: {e.message}")
            
            if e.error_code == ErrorCode.AUTH_INVALID_CREDENTIALS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"attempted_username": credentials.user_name},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            elif e.error_code == ErrorCode.AUTH_ACCOUNT_INACTIVE:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"username": credentials.user_name},
                    status_code=status.HTTP_403_FORBIDDEN
                )
            elif e.error_code == ErrorCode.AUTH_VERIFICATION_REQUIRED:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={
                        "username": credentials.user_name,
                        "verification_required": True
                    },
                    status_code=status.HTTP_403_FORBIDDEN
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or ErrorCode.UNKNOWN_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"[LOGIN] Unexpected error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def request_password_reset(
        self,
        reset_request: PasswordResetRequest
    ) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        """Request password reset email."""
        try:
            logger.info(f"[PASSWORD_RESET_REQUEST] Email: {reset_request.email}")
            
            await self.auth_service.initiate_password_reset(reset_request.email)
            
            logger.info(f"[PASSWORD_RESET_REQUEST] Request processed for: {reset_request.email}")
            
            return SuccessResponse(
                message=Message.PASSWORD_RESET_REQUEST_PROCESSING_MSG,
                data=PasswordResetResponse(
                    message=Message.PASSWORD_RESET_PROCESSED_MSG,
                    success=True
                )
            )
            
        except Exception as e:
            logger.error(f"[PASSWORD_RESET_REQUEST] Unexpected error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def reset_password(
        self,
        reset_data: PasswordResetConfirm
    ) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        """Reset password with token."""
        try:
            logger.info(f"[RESET_PASSWORD] Resetting password for: {reset_data.email}")
            
            success = await self.auth_service.reset_password(
                reset_data.email,
                reset_data.token,
                reset_data.new_password
            )
            
            if success:
                logger.info(f"[RESET_PASSWORD] Success for: {reset_data.email}")
                return SuccessResponse(
                    message=Message.PASSWORD_RESET_SUCCESS_MSG,
                    data=PasswordResetResponse(
                        message=Message.PASSWORD_RESET_SUCCESSFUL_MSG,
                        success=True
                    )
                )
            else:
                logger.warning(f"[RESET_PASSWORD] Failed for: {reset_data.email}")
                return ErrorResponse(
                    message=Message.AUTH_RESET_PASSWORD_FAILED_MSG,
                    error_code=ErrorCode.PASSWORD_RESET_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
        except AppBaseException as e:
            logger.error(f"[RESET_PASSWORD] AppBaseException: {e.message}")
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.PASSWORD_RESET_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"[RESET_PASSWORD] Unexpected error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def refresh_token(
        self,
        refresh_request
    ) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        """Refresh access token using refresh token."""
        try:
            logger.info("[REFRESH_TOKEN] Refreshing token")
            
            payload = jwt_handler.verify_token(refresh_request.refresh_token)
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if token_type != "refresh":
                logger.warning("[REFRESH_TOKEN] Invalid token type")
                return ErrorResponse(
                    message=Message.AUTH_INVALID_TOKEN_TYPE_MSG,
                    error_code=ErrorCode.AUTH_INVALID_TOKEN_TYPE,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if not user_id:
                logger.warning("[REFRESH_TOKEN] Invalid token - no user_id")
                return ErrorResponse(
                    message=Message.AUTH_INVALID_TOKEN_MSG,
                    error_code=ErrorCode.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Get user information
            user = await self.auth_service.get_user_by_id(user_id)
            if not user:
                logger.warning(f"[REFRESH_TOKEN] User not found: {user_id}")
                return ErrorResponse(
                    message=Message.AUTH_USER_NOT_FOUND_MSG,
                    error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Create new tokens
            new_access_token = jwt_handler.create_access_token(subject=str(user_id))
            new_refresh_token = jwt_handler.create_refresh_token(subject=str(user_id))

            user_response = UserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                full_name=user.profile.full_name if user.profile else None,
                phone=user.profile.phone if user.profile else None,
                gender=user.profile.gender if user.profile else None,
                avatar_url=user.profile.avatar_url if user.profile else None
            )

            token_response = TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                user=user_response
            )

            logger.info(f"[REFRESH_TOKEN] Success: {user_id}")
            
            return SuccessResponse(
                message=Message.TOKEN_REFRESH_SUCCESS_MSG,
                data=token_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[REFRESH_TOKEN] Unexpected error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.AUTH_INVALID_REFRESH_TOKEN_MSG,
                error_code=ErrorCode.INVALID_REFRESH_TOKEN,
                error_details={"error": str(e)},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

    async def logout_user(self, token: str) -> SuccessResponse[dict]:
        """Logout user and revoke token."""
        try:
            logger.info("[LOGOUT] Processing logout")
            
            payload = jwt_handler.verify_token(token)
            jti = payload.get("jti")
            
            if jti:
                blacklist_token(jti)
                logger.info("[LOGOUT] Token revoked successfully")
                
                return SuccessResponse(
                    message=Message.USER_LOGOUT_SUCCESS_MSG,
                    data={
                        "logout_time": datetime.now(timezone.utc).isoformat(),
                        "message": Message.TOKEN_REVOKED_MSG
                    }
                )
                
        except Exception as e:
            logger.warning(f"[LOGOUT] Token verification failed, but continuing logout: {e}")
            
        return SuccessResponse(
            message=Message.USER_LOGOUT_SUCCESS_MSG,
            data={
                "logout_time": datetime.now(timezone.utc).isoformat(),
                "message": Message.SESSION_TERMINATED_MSG
            }
        )

    async def health_check(self) -> SuccessResponse[dict]:
        """Health check for auth service."""
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
                    "email_verification": True 
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def change_password(
        self,
        current_user: User,
        password_data: ChangePasswordRequest
    ) -> Union[SuccessResponse[ChangePasswordResponse], ErrorResponse]:
        """Change password for authenticated user."""
        try:
            logger.info(f"[CHANGE_PASSWORD] User: {current_user.user_id}")
            
            success = await self.auth_service.change_password(
                user_id=current_user.user_id,
                old_password=password_data.old_password,
                new_password=password_data.new_password
            )

            if success:
                logger.info(f"[CHANGE_PASSWORD] Success: {current_user.user_id}")
                return SuccessResponse(
                    message=Message.PASSWORD_CHANGE_SUCCESS_MSG,
                    data=ChangePasswordResponse(
                        message=Message.PASSWORD_CHANGED_MSG,
                        success=True
                    )
                )
            else:
                logger.warning(f"[CHANGE_PASSWORD] Failed: {current_user.user_id}")
                return ErrorResponse(
                    message=Message.AUTH_CHANGE_PASSWORD_FAILED_MSG,
                    error_code=ErrorCode.PASSWORD_CHANGE_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
        except AppBaseException as e:
            logger.error(f"[CHANGE_PASSWORD] AppBaseException: {e.message}")
            
            if e.error_code == ErrorCode.AUTH_PASSWORD_WEAK:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"requirements": Message.PASSWORD_REQUIREMENTS},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            elif e.error_code == ErrorCode.AUTH_INVALID_CREDENTIALS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"field": "old_password"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or ErrorCode.PASSWORD_CHANGE_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"[CHANGE_PASSWORD] Unexpected error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============ Email Verification Endpoints ============= 
# Uncomment and refactor when needed
#
#     async def verify_email(
#         self,
#         verification_data: EmailVerificationRequest
#     ) -> Union[SuccessResponse[EmailVerificationResponse], ErrorResponse]:
#         """Verify user email with token."""
#         try:
#             logger.info(f"[VERIFY_EMAIL] Starting email verification for {verification_data.email}")
#             
#             success = await self.auth_service.verify_email(
#                 verification_data.email,
#                 verification_data.token
#             )
#             
#             if success:
#                 response = EmailVerificationResponse(
#                     message=Message.EMAIL_VERIFICATION_SUCCESS_MSG,
#                     is_verified=True
#                 )
# 
#                 logger.info(f"[VERIFY_EMAIL] Success for {verification_data.email}")
#                 return SuccessResponse(
#                     message=Message.EMAIL_VERIFICATION_SUCCESS_MSG,
#                     data=response
#                 )
#             else:
#                 logger.error(f"[VERIFY_EMAIL] Verification returned False for {verification_data.email}")
#                 return ErrorResponse(
#                     message=Message.AUTH_VERIFICATION_FAILED_MSG,
#                     error_code=ErrorCode.EMAIL_VERIFICATION_FAILED,
#                     error_details={"email": verification_data.email},
#                     status_code=status.HTTP_400_BAD_REQUEST
#                 )
# 
#         except AppBaseException as e:
#             logger.error(f"[VERIFY_EMAIL] AppBaseException: {e.message}")
#             return ErrorResponse(
#                 message=e.message,
#                 error_code=e.error_code or ErrorCode.EMAIL_VERIFICATION_FAILED,
#                 error_details={
#                     "email": verification_data.email,
#                     "verification_failed": True
#                 },
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )
# 
#         except Exception as e:
#             logger.error(f"[VERIFY_EMAIL] Unexpected error: {e}", exc_info=True)
#             return ErrorResponse(
#                 message=Message.AUTH_VERIFICATION_SYSTEM_ERROR_MSG,
#                 error_code=ErrorCode.SYSTEM_ERROR,
#                 error_details={
#                     "email": verification_data.email,
#                     "error": str(e)
#                 },
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#         
#     async def resend_verification_email(
#         self,
#         email: str
#     ) -> Union[SuccessResponse[dict], ErrorResponse]:
#         """Resend verification email."""
#         try:
#             logger.info(f"[RESEND_VERIFICATION] Email: {email}")
#             
#             result = await self.auth_service.resend_verification_email(email)
#             
#             if result:
#                 logger.info(f"[RESEND_VERIFICATION] Success for: {email}")
#                 return SuccessResponse(
#                     message=Message.EMAIL_VERIFICATION_SENT_MSG,
#                     data={
#                         "email": email,
#                         "message": Message.VERIFICATION_EMAIL_SENT_MSG
#                     }
#                 )
#             else:
#                 logger.warning(f"[RESEND_VERIFICATION] Failed for: {email}")
#                 return ErrorResponse(
#                     message=Message.AUTH_EMAIL_SEND_FAILED_MSG,
#                     error_code=ErrorCode.EMAIL_SEND_FAILED,
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
#                 
#         except AppBaseException as e:
#             logger.error(f"[RESEND_VERIFICATION] AppBaseException: {e.message}")
#             return ErrorResponse(
#                 message=e.message,
#                 error_code=e.error_code or ErrorCode.EMAIL_SEND_FAILED,
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )
#         except Exception as e:
#             logger.error(f"[RESEND_VERIFICATION] Unexpected error: {e}", exc_info=True)
#             return ErrorResponse(
#                 message=Message.INTERNAL_ERROR_MSG,
#                 error_code=ErrorCode.INTERNAL_ERROR,
#                 error_details={"error": str(e)},
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
# 
# ============ Email Verification Endpoints =============