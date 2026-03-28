import asyncio
import logging
import random
from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Optional, Protocol

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import JWTHandler
from app.core.security.password import hash_password, verify_password
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService
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
from app.modules.users.models.user import User
from app.modules.auth.models.verification_token import VerificationToken
from app.modules.auth.repository.token_repository import TokenRepository
from app.modules.auth.repository.user_repository import UserRepository
from app.modules.auth.schemas.api import UserCreate, UserLogin
from app.modules.users.models.user_profile import UserProfile
from app.shared.exceptions import BadRequestError
from app.modules.auth.utils.auth_validators import (
    validate_email,
    validate_password_strength,
    validate_username,
)


class EmailServiceProtocol(Protocol):

    def generate_verification_token(self) -> str: ...
    async def send_verification_email_async(self, email: str, token: str) -> None: ...
    async def send_password_reset_email_async(self, email: str, token: str) -> None: ...
    async def send_password_reset_success_notification_async(
        self, email: str, username: str
    ) -> None: ...
    async def send_password_changed_notification_async(
        self, email: str, username: str
    ) -> None: ...


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: TokenRepository,
        db: AsyncSession,
        email_service: EmailServiceProtocol,
        audit_repo: Optional[AuditRepository] = None,
    ) -> None:
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.db = db
        self.email_service = email_service
        self.audit_service = AuditService(audit_repo) if audit_repo else None
        self.jwt_handler = JWTHandler()

    async def _audit(
        self,
        *,
        action: str,
        success: bool,
        user_id: Optional[UUID] = None,
        resource_id: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        if not self.audit_service:
            return
        try:
            await self.audit_service.log_event(
                action=action,
                user_id=user_id,
                success=success,
                resource_type="user",
                resource_id=resource_id or (str(user_id) if user_id else None),
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error_message,
                details=details,
            )
        except Exception:
            pass


    async def register_user(
        self,
        user_data: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        self._validate_registration(user_data)

        if await self.user_repo.email_exists(user_data.email):
            raise EmailExistsError(user_data.email)

        if await self.user_repo.username_exists(user_data.user_name):
            raise UsernameExistsError(user_data.user_name)

        now = _now()
        user = User(
            user_name=user_data.user_name,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            is_active=True,
            is_verified=True,  
            is_deleted=False,
            token_version=0,
            created_at=now,
            updated_at=now,
        )

        profile = UserProfile(
            full_name=user_data.user_name,
            gender=user_data.gender,
            created_at=now,
            updated_at=now,
        )

        user = await self.user_repo.create_with_profile(
            user=user, 
            profile=profile,
            default_role_name="user"
        )
        await self.db.flush()

        await self._audit(
            action="register",
            success=True,
            user_id=user.user_id,
            details={"email": user_data.email, "user_name": user_data.user_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user


    async def login(
        self,
        form_data: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        try:
            user = await self.authenticate_user(form_data.user_name, form_data.password)
        except (InvalidCredentialsError, AccountInactiveError, AccountUnverifiedError) as e:
            await self._audit(
                action="login",
                success=False,
                error_message=str(e),
                details={"user_name": form_data.user_name},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise

        token_version = await self.get_user_token_version(user.user_id) or 0

        permissions: list = []
        if user.user_roles:
            for ur in user.user_roles:
                if ur.role and hasattr(ur.role, "permissions"):
                    permissions.extend(ur.role.permissions or [])

        tokens = self.jwt_handler.create_token_pair(
            subject=str(user.user_id),
            token_version=token_version,
            additional_claims={"permissions": permissions} if permissions else None,
        )

        await self.create_token_family(
            user_id=user.user_id,
            refresh_jti=tokens["refresh_jti"],
            access_jti=tokens["access_jti"],
            refresh_exp=tokens["refresh_exp"],
        )

        await self._audit(
            action="login",
            success=True,
            user_id=user.user_id,
            details={"user_name": form_data.user_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": user,
            "token_type": "bearer",
        }

    async def authenticate_user(
        self,
        user_name: str,
        password: str,
    ) -> User:
        user = await self.user_repo.get_by_username(user_name)
        if not user:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        if not user.is_verified:
            raise AccountUnverifiedError()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        await self.user_repo.update_last_activity(user.user_id)
        await self.db.flush()

        updated_user = await self.user_repo.get_by_id_with_details(user.user_id)
        if not updated_user:
            raise InvalidCredentialsError()

        return updated_user


    async def get_user_token_version(
        self,
        user_id: UUID,
    ) -> int:
        return await self.user_repo.get_token_version(user_id)

    async def create_token_family(
        self,
        *,
        user_id: UUID,
        refresh_jti: str,
        access_jti: str,
        refresh_exp: datetime,
        parent_jti: Optional[str] = None,
    ) -> None:
        await self.token_repo.create_token_family(
            user_id=user_id,
            refresh_jti=refresh_jti,
            access_jti=access_jti,
            expires_at=refresh_exp,
            parent_jti=parent_jti,
        )
        await self.db.flush()

    async def check_token_reuse(self, refresh_jti: str) -> None:
        if await self.token_repo.is_family_revoked(refresh_jti):
            await self.token_repo.revoke_entire_chain(refresh_jti)
            await self.db.flush()
            raise TokenReuseError()

    async def validate_token_version(
        self,
        user_id: UUID,
        token_version: int,
    ) -> None:
        current = await self.user_repo.get_token_version(user_id)
        if current is None or token_version < current:
            raise TokenRevokedError()

    async def revoke_token_family(self, jti: str) -> int:
        count = await self.token_repo.revoke_family(jti)
        await self.db.flush()
        return count

    async def refresh_token(self, refresh_token: str) -> dict:
        user_uuid: Optional[UUID] = None
        try:
            payload = self.jwt_handler.decode_token(refresh_token, verify_exp=True)
            user_id = payload.get("sub")
            token_type = payload.get("type")
            token_version = payload.get("ver", 0)
            old_jti = payload.get("jti")

            if token_type != "refresh" or not user_id or not old_jti:
                raise InvalidTokenError("Token không hợp lệ hoặc thiếu thông tin")

            # 2. Check reuse
            await self.check_token_reuse(old_jti)

            # 3. Validate version
            user_uuid = UUID(user_id)
            await self.validate_token_version(user_uuid, token_version)

            # 4. Revoke old family
            await self.revoke_token_family(old_jti)

            # 5. Get user
            user = await self.get_user_by_id(user_uuid)
            if not user:
                raise UserNotFoundError(str(user_id))

            # 6. Create new pair
            current_version = await self.get_user_token_version(user_uuid) or 0
            new_tokens = self.jwt_handler.create_token_pair(
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

            await self._audit(
                action="refresh_token",
                success=True,
                user_id=user_uuid,
            )

            return {
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens["refresh_token"],
                "user": user,
            }

        except Exception as e:
            await self._audit(
                action="refresh_token",
                success=False,
                user_id=user_uuid,
                error_message=str(e),
            )
            raise

    async def logout(
        self,
        token: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        revoked_count = 0

        try:
            payload = self.jwt_handler.decode_token(token, verify_exp=False)
            jti = payload.get("jti")
            token_user_id = payload.get("sub")

            if token_user_id:
                user_id = token_user_id

            if jti:
                revoked_count = await self.revoke_token_family(jti)
        except Exception:
            pass

        await self._audit(
            action="logout",
            success=True,
            user_id=UUID(str(user_id)) if user_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "logout_time": now_iso,
            "tokens_revoked": revoked_count,
            "message": f"Đã thu hồi {revoked_count} token"
            if revoked_count
            else "Phiên đã kết thúc",
        }

    async def revoke_all_user_tokens(
        self,
        user_id: UUID,
    ) -> dict:
        result = await self.user_repo.increment_token_version(user_id)
        await self.db.flush()

        if not result:
            raise UserNotFoundError(str(user_id))

        old_version, new_version = result
        return {
            "success": True,
            "user_id": str(user_id),
            "old_version": old_version,
            "new_version": new_version,
            "message": "Tất cả token đã bị thu hồi. "
            "Người dùng phải đăng nhập lại.",
        }

    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> User:
        return await self.user_repo.get_by_id_with_details(user_id)

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        return await self.user_repo.get_by_email(email)


    async def initiate_password_reset(self, email: str) -> bool:
        user = await self.user_repo.get_by_email(email)
        if not user:
            delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            return True

        reset_token = self.email_service.generate_verification_token()

        await self.token_repo.invalidate_previous_tokens(
            email, "password_reset"
        )

        token_entity = VerificationToken.create_token(
            email=email,
            token_type="password_reset",
            expires_in_hours=1,
        )
        token_entity.token = reset_token
        await self.token_repo.create_verification_token(token_entity)
        await self.db.flush()

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
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        validation_msg = validate_password_strength(
            new_password, email=email
        )
        if validation_msg:
            raise WeakPasswordError(validation_msg)

        token_entity = (
            await self.token_repo.get_valid_verification_token(
                email, token, "password_reset"
            )
        )
        if not token_entity:
            raise InvalidResetTokenError()

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError(email)

        await self.token_repo.mark_token_used(token_entity.token_id)

        user.hashed_password = hash_password(new_password)
        user.updated_at = _now()
        await self.db.flush()

        await self._audit(
            action="password_reset",
            success=True,
            user_id=user.user_id,
            details={"email": email},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._fire_and_forget(
            self.email_service.send_password_reset_success_notification_async(
                user.email,
                user.user_name or "",
            ),
            "xác nhận đặt lại mật khẩu",
            user.email,
        )

        return True

    async def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        user = await self.user_repo.get_by_id_with_details(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        validation_msg = validate_password_strength(
            new_password,
            username=user.user_name,
            email=user.email,
        )
        if validation_msg:
            raise WeakPasswordError(validation_msg)

        if not verify_password(old_password, user.hashed_password):
            raise InvalidCurrentPasswordError()

        user.hashed_password = hash_password(new_password)
        user.updated_at = _now()
        await self.db.flush()

        await self._audit(
            action="change_password",
            success=True,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._fire_and_forget(
            self.email_service.send_password_changed_notification_async(
                user.email,
                user.user_name or "",
            ),
            "thay đổi mật khẩu",
            user.email,
        )

        return True


    async def cleanup_expired_tokens(self) -> dict[str, int]:
        """
        Dọn verification_tokens và token_families hết hạn.
        JWT blacklist không cần cleanup — Redis tự xóa khi TTL hết.
        """
        result = await self.token_repo.cleanup_all()
        await self.db.flush()
        return result

    async def get_cleanup_stats(self) -> dict[str, int]:
        return await self.token_repo.get_cleanup_stats()

    def _validate_registration(self, user_data: UserCreate) -> None:
        email_error = validate_email(user_data.email)
        if email_error:
            raise BadRequestError(email_error)

        username_error = validate_username(user_data.user_name)
        if username_error:
            raise BadRequestError(username_error)

        password_error = validate_password_strength(
            user_data.password,
            username=user_data.user_name,
            email=user_data.email,
        )
        if password_error:
            raise WeakPasswordError(password_error)

    @staticmethod
    def _fire_and_forget(
        coro,
        email_type: str,
        recipient: str,
    ) -> None:
        try:
            asyncio.create_task(coro)
        except Exception as e:
            logger.warning(
                "Không thể tạo task gửi email '%s' cho '%s': %s",
                email_type,
                recipient,
                e,
            )
