from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
from datetime import datetime, timezone
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.schemas.user import (
    UserCreate, 
    UserLogin, 
    UserResponse, 
    EmailVerificationRequest, 
    EmailVerificationResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)
from app.modules.auth.schemas.token import TokenResponse
from app.modules.auth.services.auth_service import AuthService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import (
    AUTH_EMAIL_EXISTS,
    AUTH_PASSWORD_WEAK,
    AUTH_INVALID_CREDENTIALS,
    AUTH_ACCOUNT_INACTIVE,
    AUTH_VERIFICATION_REQUIRED,
    USER_INVALID_DATA
)
from app.core.security import JWTHandler, blacklist_token
from app.modules.auth.models.user import User
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)
jwt_handler  = JWTHandler()

class AuthController:

    def __init__(self, db: AsyncSession) -> None:
        self.auth_service: AuthService = AuthService(db)
    
    async def register_user(self, user_data: UserCreate) -> Union[SuccessResponse[UserResponse], ErrorResponse]:
        try:
            user: User = await self.auth_service.create_user(user_data)
            
            user_response: UserResponse = UserResponse(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name or "",
                is_verified=user.is_verified,
                created_at=user.created_at,
                full_name=user.profile.full_name if user.profile else None,
                phone=user.profile.phone if user.profile else None,
                avatar_url=user.profile.avatar_url if user.profile else None
            )

            return SuccessResponse(
                message="Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.",
                data=user_response
            )

        except AppBaseException as e:
            if e.error_code == AUTH_EMAIL_EXISTS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"email": user_data.email}
                )
            elif e.error_code == AUTH_PASSWORD_WEAK:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={
                        "requirements": [
                            "Ít nhất 8 ký tự",
                            "Có chữ hoa",
                            "Có chữ thường",
                            "Có số",
                            "Có ký tự đặc biệt"
                        ]
                    }
                )
            elif e.error_code == USER_INVALID_DATA:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"validation_error": str(e)}
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or "UNKNOWN_ERROR",
                    error_details=None
                )

        except Exception as e:
            print(f"Unexpected error in register_user: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )
    
    async def login_user(self, credentials: UserLogin) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        try:
            user = await self.auth_service.authenticate_user(
                credentials.email,
                credentials.password
            )

            access_token = jwt_handler.create_access_token(subject=str(user.id))
            refresh_token = jwt_handler.create_refresh_token(subject=str(user.id))

            user_response = UserResponse(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name or "",
                is_verified=user.is_verified,
                created_at=user.created_at,
                full_name=user.profile.full_name if user.profile else None,
                phone=user.profile.phone if user.profile else None,
                avatar_url=user.profile.avatar_url if user.profile else None
            )

            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_response
            )

            return SuccessResponse(
                message="Đăng nhập thành công",
                data=token_response
            )

        except AppBaseException as e:
            if e.error_code == AUTH_INVALID_CREDENTIALS:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"attempted_email": credentials.email}
                )
            elif e.error_code == AUTH_ACCOUNT_INACTIVE:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"email": credentials.email}
                )
            elif e.error_code == AUTH_VERIFICATION_REQUIRED:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={
                        "email": credentials.email,
                        "verification_required": True
                    }
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or "UNKNOWN_ERROR",
                    error_details=None
                )

        except Exception as e:
            print(f"Unexpected error in login_user: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )
    
    async def verify_email(self, verification_data: EmailVerificationRequest) -> Union[SuccessResponse[EmailVerificationResponse], ErrorResponse]:
        try:
            logger.info(f"Controller: Starting email verification for {verification_data.email}")
            
            success = await self.auth_service.verify_email(
                verification_data.email,
                verification_data.token
            )
            
            if success:
                response = EmailVerificationResponse(
                    message="Email đã được xác thực thành công! Bạn có thể đăng nhập ngay bây giờ.",
                    is_verified=True
                )

                logger.info(f"Controller: Email verification successful for {verification_data.email}")
                return SuccessResponse(
                    message="Xác thực email thành công",
                    data=response
                )
            else:
                logger.error(f"Controller: Email verification returned False for {verification_data.email}")
                return ErrorResponse(
                    message="Xác thực email thất bại",
                    error_code=AUTH_INVALID_CREDENTIALS,
                    error_details={"email": verification_data.email}
                )

        except AppBaseException as e:
            logger.error(f"Controller: AppBaseException during verification: {e.message}")
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or AUTH_INVALID_CREDENTIALS,
                error_details={
                    "email": verification_data.email,
                    "verification_failed": True,
                    "error_type": "AppBaseException"
                }
            )

        except Exception as e:
            logger.error(f"Controller: Unexpected error during verification: {str(e)}")
            return ErrorResponse(
                message="Xác thực email thất bại do lỗi hệ thống",
                error_code="SYSTEM_ERROR",
                error_details={
                    "email": verification_data.email,
                    "error": str(e),
                    "error_type": "UnexpectedException"
                }
            )

    async def request_password_reset(self, reset_request: PasswordResetRequest) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        try:
            await self.auth_service.initiate_password_reset(reset_request.email)
            
            return SuccessResponse(
                message="Nếu email tồn tại, một liên kết đặt lại mật khẩu đã được gửi đến địa chỉ email của bạn.",
                data=PasswordResetResponse(
                    message="Password reset request processed",
                    success=True
                )
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in request_password_reset: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )

    async def reset_password(self, reset_data: PasswordResetConfirm) -> Union[SuccessResponse[PasswordResetResponse], ErrorResponse]:
        try:
            success = await self.auth_service.reset_password(
                reset_data.email,
                reset_data.token,
                reset_data.new_password
            )
            
            if success:
                return SuccessResponse(
                    message="Mật khẩu đã được cập nhật thành công.",
                    data=PasswordResetResponse(
                        message="Password reset successful",
                        success=True
                    )
                )
            else:
                return ErrorResponse(
                    message="Không thể đặt lại mật khẩu",
                    error_code="PASSWORD_RESET_ERROR",
                    error_details=None
                )
            
        except AppBaseException as e:
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or "PASSWORD_RESET_ERROR",
                error_details=None
            )
        except Exception as e:
            logger.error(f"Unexpected error in reset_password: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )

    async def refresh_token(self, refresh_request) -> Union[SuccessResponse[TokenResponse], ErrorResponse]:
        try:
            payload = jwt_handler.verify_token(refresh_request.refresh_token)
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Create new tokens
            new_access_token = jwt_handler.create_access_token(subject=str(user_id))
            new_refresh_token = jwt_handler.create_refresh_token(subject=str(user_id))
            
            user_response = UserResponse(
                user_id=user_id,
                email="",  
                display_name="",
                is_verified=False,
                created_at=datetime.now(timezone.utc)
            )
            
            token_response = TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token, 
                user=user_response
            )
            
            return SuccessResponse(
                message="Token refreshed successfully",
                data=token_response
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def logout_user(self, token: str) -> SuccessResponse[dict]:
        try:
            payload = jwt_handler.verify_token(token)

            jti = payload.get("jti")
            if jti:

                blacklist_token(jti)
            
            return SuccessResponse(
                message="Đăng xuất thành công",
                data={
                    "logout_time": datetime.now(timezone.utc),
                    "message": "Token has been revoked"
                }
            )
        except Exception as e:
            return SuccessResponse(
                message="Đăng xuất thành công",
                data={
                    "logout_time": datetime.now(timezone.utc),
                    "message": "Session terminated"
                }
            )

    async def resend_verification_email(self, email: str) -> Union[SuccessResponse[dict], ErrorResponse]:
        try:
            result = await self.auth_service.resend_verification_email(email)
            
            if result:
                return SuccessResponse(
                    message="Email xác thực đã được gửi lại thành công",
                    data={"email": email, "message": "Verification email sent"}
                )
            else:
                return ErrorResponse(
                    message="Không thể gửi lại email xác thực",
                    error_code="EMAIL_SEND_FAILED",
                    error_details=None
                )
                
        except AppBaseException as e:
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or "EMAIL_SEND_FAILED",
                error_details=None
            )
        except Exception as e:
            logger.error(f"Unexpected error in resend_verification_email: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )

    async def health_check(self) -> SuccessResponse[dict]:
        return SuccessResponse(
            message="Auth service đang hoạt động bình thường",
            data={
                "service": "auth",
                "status": "healthy",
                "features": {
                    "user_registration": True,
                    "user_authentication": True,
                    "jwt_tokens": True,
                    "email_verification": True 
                }
            }
        )