"""
AuthService — Service thống nhất cho auth module.

Gộp logic từ: UserService, AuthenticationService, PasswordService.
Dùng repository pattern thay raw SQL. Raise AppException thay HTTPException.
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.Security.password import hash_password, verify_password
from app.modules.auth.exceptions import (
    AccountInactiveError,
    AccountUnverifiedError,
    EmailExistsError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidResetTokenError,
    InvalidTokenError,
    TokenReuseError,
    TokenRevokedError,
    UserNotFoundError,
    UsernameExistsError,
    WeakPasswordError,
)
from app.modules.auth.models.user import User
from app.modules.auth.models.verification_token import VerificationToken
from app.modules.auth.repository.token_repository import TokenRepository
from app.modules.auth.repository.user_repository import UserRepository
from app.modules.auth.schemas.api import UserCreate
from app.modules.profile.models.user_profile import UserProfile
from app.utils.validators.auth_validators import (
    validate_email,
    validate_password_strength,
    validate_username,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    """UTC hiện tại không có tzinfo (match database format)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    """
    Service thống nhất cho auth module.

    Quản lý: đăng ký, đăng nhập, mật khẩu, token lifecycle.
    Raise exception thay vì trả ErrorResponse.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: TokenRepository,
        db: AsyncSession,
        email_service: Any,
    ) -> None:
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.db = db
        self.email_service = email_service

    # ══════════════════════════════════════════════════════
    # REGISTRATION
    # ══════════════════════════════════════════════════════

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Đăng ký user mới với full validation.

        Raises:
            WeakPasswordError: Mật khẩu yếu
            EmailExistsError: Email đã tồn tại
            UsernameExistsError: Username đã tồn tại
        """
        # Validate
        self._validate_registration(user_data)

        # Check duplicates
        if await self.user_repo.email_exists(user_data.email):
            raise EmailExistsError(user_data.email)

        if await self.user_repo.username_exists(user_data.user_name):
            raise UsernameExistsError(user_data.user_name)

        # Create user entity
        now = _now()
        user = User(
            user_name=user_data.user_name,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            is_active=True,
            is_verified=False,
            is_deleted=False,
            token_version=0,
            created_at=now,
            updated_at=now,
        )

        # Create profile entity
        profile = UserProfile(
            full_name=user_data.user_name,
            gender=user_data.gender,
            created_at=now,
            updated_at=now,
        )

        # Persist user + profile + default role
        user = await self.user_repo.create_with_profile(user, profile)
        await self.db.commit()

        # Gửi email xác thực (fire-and-forget)
        await self._send_verification_email(user)

        logger.info("User đã đăng ký thành công: %s", user.user_id)
        return user

    # ══════════════════════════════════════════════════════
    # AUTHENTICATION
    # ══════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════
    # LOGIN / AUTH
    # ══════════════════════════════════════════════════════

    async def login(self, form_data) -> dict:
        """
        Xử lý đăng nhập hoàn chỉnh: Auth -> Token Generation -> Family Creation.
        """
        # 1. Authenticate (check username/pass, active, verified)
        user = await self.authenticate_user(form_data.username, form_data.password)

        # 2. Generate Tokens
        from app.core.Security.jwt import JWTHandler
        jwt_handler = JWTHandler()

        token_version = await self.get_user_token_version(user.user_id) or 0
        tokens = jwt_handler.create_token_pair(
            subject=str(user.user_id),
            token_version=token_version,
            permissions=user.role.permissions if user.role else []
        )

        # 3. Create Token Family
        await self.create_token_family(
            user_id=user.user_id,
            refresh_jti=tokens["refresh_jti"],
            access_jti=tokens["access_jti"],
            refresh_exp=tokens["refresh_exp"]
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": user,
            "token_type": "bearer"
        }

    async def authenticate_user(
        self,
        user_name: str,
        password: str,
    ) -> User:
        """
        Xác thực user với username và password.

        Raises:
            InvalidCredentialsError: Sai username/password
            AccountInactiveError: Tài khoản bị vô hiệu hóa
            AccountUnverifiedError: Chưa xác minh tài khoản
        """
        user = await self.user_repo.get_by_username(user_name)
        if not user:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        if not user.is_verified:
            raise AccountUnverifiedError()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        # Update last activity
        await self.user_repo.update_last_activity(user.user_id)
        await self.db.commit()

        # Reload với full details
        updated_user = await self.user_repo.get_by_id_with_details(
            user.user_id
        )
        if not updated_user:
            raise InvalidCredentialsError()

        logger.info("User đã xác thực thành công: %s", user_name)
        return updated_user

    # ... (Keep other methods)

    # ══════════════════════════════════════════════════════
    # TOKEN MANAGEMENT
    # ══════════════════════════════════════════════════════

    async def get_user_token_version(
        self,
        user_id: uuid.UUID,
    ) -> Optional[int]:
        """Lấy token_version hiện tại."""
        return await self.user_repo.get_token_version(user_id)

    async def create_token_family(
        self,
        *,
        user_id: uuid.UUID,
        refresh_jti: str,
        access_jti: str,
        refresh_exp: datetime,
        parent_jti: Optional[str] = None,
    ) -> None:
        """Tạo token family mới."""
        await self.token_repo.create_token_family(
            user_id=user_id,
            refresh_jti=refresh_jti,
            access_jti=access_jti,
            expires_at=refresh_exp,
            parent_jti=parent_jti,
        )
        await self.db.commit()

    async def check_token_reuse(self, refresh_jti: str) -> None:
        """
        Kiểm tra token reuse. Nếu phát hiện → revoke chain + raise.

        Raises:
            TokenReuseError: Phát hiện tái sử dụng token
        """
        if await self.token_repo.is_family_revoked(refresh_jti):
            logger.error(
                "[SECURITY] Token reuse detected: jti=%s", refresh_jti
            )
            await self.token_repo.revoke_entire_chain(refresh_jti)
            await self.db.commit()
            raise TokenReuseError()

    async def validate_token_version(
        self,
        user_id: uuid.UUID,
        token_version: int,
    ) -> None:
        """
        Kiểm tra token_version còn hợp lệ.

        Raises:
            TokenRevokedError: Token đã bị thu hồi qua version mismatch
        """
        current = await self.user_repo.get_token_version(user_id)
        if current is None or token_version < current:
            raise TokenRevokedError()

    async def revoke_token_family(self, jti: str) -> int:
        """Thu hồi 1 token family."""
        count = await self.token_repo.revoke_family(jti)
        await self.db.commit()
        return count

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Làm mới access token (logic đầy đủ).

        Steps:
        1. Decode & Validate token
        2. Check reuse
        3. Revoke old family
        4. Create new token pair & family

        Returns:
            dict: {
                "access_token": str,
                "refresh_token": str,
                "user": User
            }
        """
        from app.core.Security.jwt import JWTHandler
        jwt_handler = JWTHandler()

        # 1. Decode & Validate
        payload = jwt_handler.decode_token(refresh_token, verify_exp=True)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        token_version = payload.get("ver", 0)
        old_jti = payload.get("jti")

        if token_type != "refresh" or not user_id or not old_jti:
            raise InvalidTokenError("Token không hợp lệ hoặc thiếu thông tin")

        # 2. Check reuse
        await self.check_token_reuse(old_jti)

        # 3. Validate version
        user_uuid = uuid.UUID(user_id)
        await self.validate_token_version(user_uuid, token_version)

        # 4. Revoke old family
        await self.revoke_token_family(old_jti)

        # 5. Get user
        user = await self.get_user_by_id(user_uuid)
        if not user:
            raise UserNotFoundError(str(user_id))

        # 6. Create new pair
        current_version = await self.get_user_token_version(user_uuid) or 0
        new_tokens = jwt_handler.create_token_pair(
            subject=user_id, token_version=current_version
        )

        # 7. Create new family
        await self.create_token_family(
            user_id=user_uuid,
            refresh_jti=new_tokens["refresh_jti"],
            access_jti=new_tokens["access_jti"],
            refresh_exp=new_tokens["refresh_exp"],
            parent_jti=old_jti,
        )

        return {
            "access_token": new_tokens["access_token"],
            "refresh_token": new_tokens["refresh_token"],
            "user": user
        }

    async def revoke_all_user_tokens(
        self,
        user_id: uuid.UUID,
    ) -> dict:
        """
        Thu hồi tất cả tokens bằng cách tăng token_version.

        Returns:
            Dict chứa old_version, new_version, message
        """
        result = await self.user_repo.increment_token_version(user_id)
        await self.db.commit()

        if not result:
            raise UserNotFoundError(str(user_id))

        old_version, new_version = result
        logger.info(
            "Đã thu hồi tất cả tokens cho user %s: v%s -> v%s",
            user_id,
            old_version,
            new_version,
        )
        return {
            "success": True,
            "user_id": str(user_id),
            "old_version": old_version,
            "new_version": new_version,
            "message": "Tất cả token đã bị thu hồi. "
            "Người dùng phải đăng nhập lại.",
        }

    # ══════════════════════════════════════════════════════
    # USER RETRIEVAL
    # ══════════════════════════════════════════════════════

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        """Lấy user theo ID kèm profile + roles."""
        return await self.user_repo.get_by_id_with_details(user_id)

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        """Lấy user theo email."""
        return await self.user_repo.get_by_email(email)

    # ══════════════════════════════════════════════════════
    # PASSWORD MANAGEMENT
    # ══════════════════════════════════════════════════════

    async def initiate_password_reset(self, email: str) -> bool:
        """
        Khởi tạo password reset — tạo token và gửi email.

        Luôn trả True để không reveal email tồn tại hay không.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Security: don't reveal if email exists
            delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            return True

        reset_token = self.email_service.generate_verification_token()

        # Vô hiệu hóa token cũ
        await self.token_repo.invalidate_previous_tokens(
            email, "password_reset"
        )

        # Tạo token mới
        token_entity = VerificationToken.create_token(
            email=email,
            token_type="password_reset",
            expires_in_hours=1,
        )
        # Override token value với token từ email service
        token_entity.token = reset_token
        await self.token_repo.create_verification_token(token_entity)
        await self.db.commit()

        logger.info("Token đặt lại mật khẩu đã được tạo cho: %s", email)

        # Fire-and-forget email
        self._fire_and_forget(
            self.email_service.send_password_reset_email_async(
                email, reset_token),
            "đặt lại mật khẩu",
            email,
        )

        return True

    async def reset_password(
        self,
        email: str,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Đặt lại mật khẩu dựa trên token.

        Raises:
            WeakPasswordError: Mật khẩu yếu
            InvalidResetTokenError: Token không hợp lệ hoặc hết hạn
        """
        # Validate password strength
        validation_msg = validate_password_strength(
            new_password, email=email
        )
        if validation_msg:
            raise WeakPasswordError(validation_msg)

        # Verify token
        token_entity = (
            await self.token_repo.get_valid_verification_token(
                email, token, "password_reset"
            )
        )
        if not token_entity:
            raise InvalidResetTokenError()

        if token_entity.is_expired:
            raise InvalidResetTokenError()

        # Mark token as used
        await self.token_repo.mark_token_used(token_entity.token_id)

        # Update password
        user = await self.user_repo.get_by_email(email)
        if user:
            user.hashed_password = hash_password(new_password)
            user.updated_at = _now()
            await self.db.flush()

        await self.db.commit()

        logger.info("Đặt lại mật khẩu thành công cho user: %s", email)
        return True

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        Đổi mật khẩu (verify mật khẩu cũ trước).

        Raises:
            UserNotFoundError: Không tìm thấy user
            WeakPasswordError: Mật khẩu mới yếu
            InvalidCurrentPasswordError: Mật khẩu hiện tại sai
        """
        user = await self.user_repo.get_by_id_with_details(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        # Validate new password
        validation_msg = validate_password_strength(
            new_password,
            username=user.user_name,
            email=user.email,
        )
        if validation_msg:
            raise WeakPasswordError(validation_msg)

        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCurrentPasswordError()

        # Update password
        user.hashed_password = hash_password(new_password)
        user.updated_at = _now()
        await self.db.flush()
        await self.db.commit()

        # Send notification email (fire-and-forget)
        self._fire_and_forget(
            self.email_service.send_password_changed_notification_async(
                user.email,
                user.user_name or "",
            ),
            "thay đổi mật khẩu",
            user.email,
        )

        logger.info(
            "Mật khẩu đã được thay đổi thành công cho user: %s", user_id
        )
        return True

    # ══════════════════════════════════════════════════════
    # TOKEN CLEANUP (delegated to TokenRepository)
    # ══════════════════════════════════════════════════════

    async def cleanup_expired_tokens(self) -> dict[str, int]:
        """Dọn dẹp tất cả expired tokens."""
        result = await self.token_repo.cleanup_all()
        await self.db.commit()
        return result

    async def get_cleanup_stats(self) -> dict[str, int]:
        """Lấy thống kê cleanup."""
        return await self.token_repo.get_cleanup_stats()

    # ══════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ══════════════════════════════════════════════════════

    def _validate_registration(self, user_data: UserCreate) -> None:
        """Validate dữ liệu đăng ký. Raise exception nếu invalid."""
        email_error = validate_email(user_data.email)
        if email_error:
            raise WeakPasswordError(email_error)

        username_error = validate_username(user_data.user_name)
        if username_error:
            raise WeakPasswordError(username_error)

        password_error = validate_password_strength(
            user_data.password,
            username=user_data.user_name,
            email=user_data.email,
        )
        if password_error:
            raise WeakPasswordError(password_error)

    async def _send_verification_email(self, user: User) -> None:
        """Gửi email xác thực (fire-and-forget)."""
        try:
            verification_token = self.email_service.generate_verification_token()

            # Tạo verification token
            token_entity = VerificationToken.create_token(
                email=user.email,
                token_type="email_verification",
                expires_in_hours=24,
            )
            token_entity.token = verification_token
            await self.token_repo.create_verification_token(token_entity)
            await self.db.commit()

            self._fire_and_forget(
                self.email_service.send_verification_email_async(
                    user.email, verification_token
                ),
                "xác thực email",
                user.email,
            )
        except Exception as e:
            # Email failure should not block registration
            logger.error(
                "Không thể gửi email xác thực cho %s: %s",
                user.email,
                str(e),
            )

    @staticmethod
    def _fire_and_forget(
        coro,
        email_type: str,
        recipient: str,
    ) -> None:
        """Fire-and-forget async email task."""
        try:
            asyncio.create_task(coro)
            logger.info(
                "Email %s đã được đưa vào hàng đợi cho: %s",
                email_type,
                recipient,
            )
        except Exception as e:
            logger.error(
                "Không thể đưa email %s vào hàng đợi cho %s: %s",
                email_type,
                recipient,
                str(e),
            )
