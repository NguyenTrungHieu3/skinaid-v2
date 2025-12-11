import uuid
import asyncio
import logging
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.core.Security.password import hash_password, verify_password
from app.modules.auth.models.verification_token import VerificationToken
from app.utils.constants.error_codes import AUTH_PASSWORD_WEAK
from app.utils.validators.auth_validators import validate_password_strength

#Import helpers and user service
from . import _helpers
from .user_service import UserService

logger = logging.getLogger(__name__)


class PasswordService:
    
    def __init__(self, db: AsyncSession, user_service: Optional[UserService] = None):
        """
        Khởi tạo PasswordService
        """
        self.db = db
        self.user_service = user_service or UserService(db)

    async def initiate_password_reset(self, email: str) -> bool:
        """
        Khởi tạo password reset - tạo token và gửi email
        """
        try:
            import random

            user = await self.user_service.get_user_by_email(email)
            if not user:
                # Security: Don't reveal if email exists
                delay = random.uniform(0.5, 2.0)
                await asyncio.sleep(delay)
                return True

            email_service = _helpers.get_email_service()
            reset_token = email_service.generate_verification_token()
            current_time = _helpers.get_current_utc_time()

            # Invalidate all old password reset tokens
            invalidate_old_tokens_sql = text(
                """
                UPDATE verification_tokens
                SET is_used = true,
                    updated_at = :updated_at
                WHERE email = :email
                  AND token_type = 'password_reset'
                  AND is_used = false
                  AND expires_at > :current_time
                """
            )

            invalidate_result = await self.db.execute(
                invalidate_old_tokens_sql,
                {
                    "email": email,
                    "updated_at": current_time,
                    "current_time": current_time,
                },
            )
            
            invalidated_count = invalidate_result.rowcount
            if invalidated_count > 0:
                logger.info(
                    "Đã vô hiệu hóa %d token reset password cũ cho email: %s",
                    invalidated_count,
                    email,
                )

            # Create new token
            token_sql = text(
                """
                INSERT INTO verification_tokens (
                    token_id,
                    email,
                    token,
                    token_type,
                    expires_at,
                    is_used,
                    created_at,
                    updated_at
                )
                VALUES (
                    :token_id,
                    :email,
                    :token,
                    :token_type,
                    :expires_at,
                    :is_used,
                    :created_at,
                    :updated_at
                )
            """
            )

            token_params = {
                "token_id": str(uuid.uuid4()),
                "email": email,
                "token": reset_token,
                "token_type": "password_reset",
                "expires_at": current_time + timedelta(hours=1),
                "is_used": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            await self.db.execute(token_sql, token_params)
            await self.db.commit()
            logger.info("Token đặt lại mật khẩu đã được tạo cho: %s", email)

            # Send email
            await _helpers.send_email_async(
                email_service.send_password_reset_email_async(email, reset_token),
                "đặt lại mật khẩu",
                email
            )

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn trong quá trình khởi tạo đặt lại mật khẩu: %s",
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khởi tạo đặt lại mật khẩu thất bại do lỗi nội bộ"
            )

    async def reset_password(
        self,
        email: str,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Đặt lại mật khẩu dựa trên token
        """
        try:
            # Validate password
            _helpers.raise_if_validation_fails(
                validate_password_strength(new_password, email=email),
                AUTH_PASSWORD_WEAK
            )

            token_sql = text(
                """
                SELECT *
                FROM verification_tokens
                WHERE email = :email
                  AND token = :token
                  AND token_type = 'password_reset'
                  AND is_used = false
            """
            )

            token_dict = await _helpers.execute_query_one(
                self.db,
                token_sql,
                {"email": email, "token": token}
            )

            if not token_dict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn"
                )

            verification_token = VerificationToken.model_validate(token_dict)

            if verification_token.is_expired:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token đặt lại mật khẩu đã hết hạn"
                )

            current_time = _helpers.get_current_utc_time()

            # Mark token as used
            await self.db.execute(
                text(
                    """
                    UPDATE verification_tokens
                    SET is_used = true,
                        updated_at = :updated_at
                    WHERE token_id = :token_id
                """
                ),
                {
                    "token_id": verification_token.token_id,
                    "updated_at": current_time,
                },
            )

            # Update password
            hashed_password = hash_password(new_password)
            await self.db.execute(
                text(
                    """
                    UPDATE users
                    SET hashed_password = :hashed_password,
                        updated_at = :updated_at
                    WHERE email = :email
                      AND is_deleted = false
                """
                ),
                {
                    "email": email,
                    "hashed_password": hashed_password,
                    "updated_at": current_time,
                },
            )

            await self.db.commit()
            logger.info("Đặt lại mật khẩu thành công cho user: %s", email)
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn trong quá trình đặt lại mật khẩu: %s",
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đặt lại mật khẩu thất bại do lỗi nội bộ"
            )

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        Đổi mật khẩu (phải verify mật khẩu cũ)
        """
        try:
            user = await self.user_service.get_user_by_id(user_id=user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không tìm thấy người dùng"
                )

            # Validate new password
            _helpers.raise_if_validation_fails(
                validate_password_strength(
                    new_password,
                    username=user.user_name,
                    email=user.email
                ),
                AUTH_PASSWORD_WEAK
            )

            # Verify old password
            if not verify_password(old_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mật khẩu hiện tại không đúng"
                )

            hashed_password = hash_password(new_password)

            # Update password
            await self.db.execute(
                text(
                    """
                    UPDATE users
                    SET hashed_password = :hashed_password,
                        updated_at = :updated_at
                    WHERE user_id = :user_id
                      AND is_deleted = false
                """
                ),
                {
                    "user_id": user_id,
                    "hashed_password": hashed_password,
                    "updated_at": _helpers.get_current_utc_time(),
                },
            )

            await self.db.commit()

            # Send notification email
            email_service = _helpers.get_email_service()
            await _helpers.send_email_async(
                email_service.send_password_changed_notification_async(
                    user.email,
                    user.user_name or "",
                ),
                "thay đổi mật khẩu",
                user.email
            )

            logger.info("Mật khẩu đã được thay đổi thành công cho user: %s", user_id)
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Lỗi không mong muốn trong quá trình thay đổi mật khẩu: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thay đổi mật khẩu thất bại do lỗi nội bộ"
            )
