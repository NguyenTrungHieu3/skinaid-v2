from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models.user import User
from app.modules.auth.models.verification_token import VerificationToken
from app.core.Security.password import hash_password
from app.modules.users.schemas.api import (
    CreateUserRequest,
    UpdateUserRequest,
    UserBasicInfo,
    UserDetailInfo,
    PaginationInfo,
    UserStatsResponse
)
from app.modules.users.repository.user_repository import UserRepository
from app.modules.auth.repository.token_repository import TokenRepository
from app.modules.users.exceptions import (
    UserManagementNotFoundError,
    UserActionFailedError
)
from app.shared.exceptions import ConflictError, BadRequestError
from app.modules.audit.services.audit_service import AuditService
from app.modules.audit.audit_repository import AuditRepository
from app.modules.users.services.user_mapper import UserMapper


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.token_repository = TokenRepository(db)
        self.db = db
        audit_repo = AuditRepository(db)
        self.audit_service = AuditService(audit_repo)

    async def _get_user_or_raise(self, user_id: UUID) -> User:
        """Get user by ID or raise UserManagementNotFoundError."""
        user = await self.repository.get_by_id(user_id)
        if not user or user.is_deleted:
            raise UserManagementNotFoundError(message=f"User {user_id} not found")
        return user

    async def _get_timestamp(self) -> int:
        """Get current timestamp for renaming deleted users."""
        return int(datetime.now().timestamp())

    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[UserBasicInfo], PaginationInfo]:
        """Get users with filters and pagination."""
        skip = (page - 1) * limit
        users, total = await self.repository.get_users_with_filters(
            skip=skip, limit=limit, search=search, role=role, status=status
        )

        user_list = [
            UserMapper.to_basic_info(user, await self.repository.get_user_upload_count(user.user_id))
            for user in users
        ]

        total_pages = (total + limit - 1) // limit if total > 0 else 1

        pagination = PaginationInfo(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )

        return user_list, pagination

    async def get_user_detail(self, user_id: UUID) -> Optional[UserDetailInfo]:
        """Get detailed user info."""
        user = await self.repository.get_user_with_details(user_id)
        if not user:
            return None

        upload_count = await self.repository.get_user_upload_count(user.user_id)
        return UserMapper.to_detail_info(user, upload_count)

    async def create_user(
        self,
        user_data: CreateUserRequest,
        current_admin: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserDetailInfo:
        """Create a new user with transaction and audit logging."""
        try:
            await self._check_and_handle_conflicts(user_data.email, user_data.user_name)
            new_user_id = await self._create_new_user_with_profile(user_data)
            await self._assign_role(new_user_id, user_data.role)
            await self.db.commit()

            new_user = await self.repository.get_by_id(new_user_id)
            if new_user:
                await self._try_send_verification_email(new_user)

            user_detail = await self.get_user_detail(new_user_id)
            if not user_detail:
                raise UserManagementNotFoundError(f"User {new_user_id} not found after creation")

            await self.audit_service.log_event(
                action="CREATE_USER",
                user_id=current_admin.user_id,
                success=True,
                resource_type="user",
                resource_id=str(new_user_id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": user_data.email},
            )

            return user_detail

        except (ConflictError, BadRequestError, UserManagementNotFoundError) as e:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise UserActionFailedError(message=f"Failed to create user: {str(e)}")

    # ══════════════════════════════════════════════════════
    # HELPER METHODS FOR CREATE_USER
    # ══════════════════════════════════════════════════════

    async def _check_and_handle_conflicts(self, email: str, username: str) -> None:
        """Check for existing users and handle soft-deleted collisions."""
        # Check Email
        if await self.repository.email_exists(email):
            existing = await self.repository.get_by_email(email)
            if existing:
                if not existing.is_deleted:
                    raise ConflictError(message="Email already registered")
                else:
                    # Rename deleted user to free up email
                    await self._rename_deleted_user(existing)

        # Check Username
        if await self.repository.username_exists(username):
            existing = await self.repository.get_by_username(username)
            if existing:
                if not existing.is_deleted:
                    raise ConflictError(
                        message=f"Username '{username}' already exists")
                else:
                    if existing.email != email:  # If it's a different user record
                        await self._rename_deleted_user(existing)

    async def _rename_deleted_user(self, user: User) -> None:
        """Rename a deleted user's unique fields to prevent conflicts."""
        timestamp = await self._get_timestamp()
        if ".deleted." not in user.email:
            user.email = f"{user.email}.deleted.{timestamp}"
        if ".deleted." not in user.user_name:
            user.user_name = f"{user.user_name}.deleted.{timestamp}"
        self.db.add(user)
        await self.db.flush()

    async def _create_new_user_with_profile(self, user_data: CreateUserRequest) -> UUID:
        """Create new User and UserProfile entities."""
        display_name = user_data.display_name or user_data.user_name
        if len(display_name.strip()) < 2:
            raise BadRequestError(
                message="Display name must be at least 2 characters")

        hashed_pw = hash_password(user_data.password)
        new_user_id = uuid4()

        new_user = User(
            user_id=new_user_id,
            user_name=user_data.user_name,
            email=user_data.email,
            hashed_password=hashed_pw,
            is_active=True,
            is_verified=True
        )
        self.db.add(new_user)
        await self.db.flush()

        # Create Profile
        await self.repository.create_profile(
            user_id=new_user_id,
            full_name=display_name.strip()
        )
        return new_user_id

    async def _assign_role(self, user_id: UUID, role_name: str) -> None:
        """Find and assign a role to a user."""
        role = await self.repository.get_role_by_name(role_name)
        if not role:
            raise UserManagementNotFoundError(
                message=f"Role '{role_name}' not found")
        await self.repository.assign_role(user_id, role.role_id)

    async def _try_send_verification_email(self, user: User) -> None:
        """Try to send verification email, silently ignore failures."""
        try:
            await self._send_verification_email(user)
        except Exception:
            pass

    async def update_user(
        self,
        user_id: UUID,
        user_data: UpdateUserRequest,
        current_admin: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[UserDetailInfo]:
        """Update user details with audit logging."""
        user = await self._get_user_or_raise(user_id)

        try:
            if user_data.user_name and user_data.user_name != user.user_name:
                if await self.repository.username_exists(user_data.user_name):
                    existing = await self.repository.get_by_username(user_data.user_name)
                    if existing and existing.user_id != user_id:
                        raise ConflictError(
                            message=f"Username '{user_data.user_name}' already exists")
                user.user_name = user_data.user_name

            if user_data.display_name is not None:
                user_with_details = await self.repository.get_user_with_details(user_id)
                if user_with_details and user_with_details.profile:
                    user_with_details.profile.full_name = user_data.display_name.strip()
                    self.db.add(user_with_details.profile)
                else:
                    await self.repository.create_profile(user_id, user_data.display_name.strip())

            if user_data.email and user_data.email != user.email:
                if await self.repository.email_exists(user_data.email):
                    existing = await self.repository.get_by_email(user_data.email)
                    if existing and existing.user_id != user_id:
                        raise ConflictError(message="Email already in use")
                user.email = user_data.email
                await self.token_repository.delete_tokens_by_email(user.email)

            if user_data.is_active is not None:
                user.is_active = user_data.is_active

            if user_data.password:
                user.hashed_password = hash_password(user_data.password)

            if user_data.role:
                await self.repository.remove_all_user_roles(user_id)
                role = await self.repository.get_role_by_name(user_data.role)
                if not role:
                    raise UserManagementNotFoundError(
                        message=f"Role '{user_data.role}' not found")
                await self.repository.assign_role(user_id, role.role_id)

            await self.db.commit()

            await self.audit_service.log_event(
                action="UPDATE_USER",
                user_id=current_admin.user_id,
                success=True,
                resource_type="user",
                resource_id=str(user_id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": user.email},
            )

            return await self.get_user_detail(user_id)

        except (ConflictError, UserManagementNotFoundError) as e:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise UserActionFailedError(message=f"Update failed: {str(e)}")

    async def delete_user(
        self,
        user_id: UUID,
        current_admin: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Soft delete user with audit logging."""
        user = await self._get_user_or_raise(user_id)

        try:
            await self.repository.soft_delete(user)
            await self._rename_deleted_user(user)
            await self.db.commit()

            await self.audit_service.log_event(
                action="DELETE_USER",
                user_id=current_admin.user_id,
                success=True,
                resource_type="user",
                resource_id=str(user_id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"deleted_email": user.email},
            )

            return True
        except UserManagementNotFoundError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise UserActionFailedError(message=f"Delete failed: {str(e)}")

    async def update_user_status(
        self,
        user_id: UUID,
        is_active: bool,
        current_admin: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[UserDetailInfo]:
        """Update user active status with audit logging."""
        user = await self._get_user_or_raise(user_id)

        try:
            user.is_active = is_active
            await self.db.commit()

            await self.audit_service.log_event(
                action="UPDATE_USER_STATUS",
                user_id=current_admin.user_id,
                success=True,
                resource_type="user",
                resource_id=str(user_id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"is_active": is_active},
            )

            return await self.get_user_detail(user_id)
        except Exception as e:
            await self.db.rollback()
            raise UserActionFailedError(message="Status update failed")

    async def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics."""
        data = await self.repository.get_user_stats()
        return UserStatsResponse(**data)

    async def _send_verification_email(self, user: User) -> None:
        """Helper to send email."""
        import os
        use_mock = os.getenv("TESTING") == "true" or os.getenv(
            "USE_MOCK_EMAIL") == "true"
        if use_mock:
            from app.shared.services.mock_email_service import mock_email_service as email_service
        else:
            from app.shared.services.email_service import email_service

        token_str = email_service.generate_verification_token()
        await self.token_repository.delete_tokens_by_email(user.email, "email_verification")
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        verification_token = VerificationToken(
            token_id=uuid4(),
            email=user.email,
            token=token_str,
            token_type="email_verification",
            expires_at=now + timedelta(hours=24),
            is_used=False,
            created_at=now,
            updated_at=now
        )

        await self.token_repository.create_verification_token(verification_token)
        await self.db.commit()
        await email_service.send_verification_email_async(user.email, token_str)

    async def resend_verification_email(
        self,
        user_id: UUID,
        current_admin: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Resend verification email with audit logging."""
        user = await self._get_user_or_raise(user_id)

        if user.is_verified:
            raise BadRequestError(message="User already verified")

        try:
            await self._send_verification_email(user)

            await self.audit_service.log_event(
                action="RESEND_VERIFICATION",
                user_id=current_admin.user_id,
                success=True,
                resource_type="user",
                resource_id=str(user_id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": user.email},
            )
            return True
        except Exception:
            return False
