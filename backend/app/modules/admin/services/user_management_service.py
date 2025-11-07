from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text, delete
from sqlmodel import col
from typing import Optional, List, Tuple
from uuid import UUID
import uuid

from app.modules.auth.models.user import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.roles import Role
from app.core.Security.password import hash_password
from app.modules.admin.schemas.user_management_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserBasicInfo,
    UserDetailInfo,
    PaginationInfo,
    UserStatsResponse
)


class UserManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[UserBasicInfo], PaginationInfo]:
        """
        Get paginated list of users with filters
        
        Args:
            page: Page number (starts from 1)
            limit: Number of records per page
            search: Search term for email or display_name
            role: Filter by role name
            status: Filter by status (active/inactive)
        
        Returns:
            Tuple of (list of users, pagination info)
        """
        # Build base query
        query = select(User).where(User.is_deleted == False)
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.display_name.ilike(search_pattern)
                )
            )
        
        # Apply status filter
        if status:
            is_active = status.lower() == 'active'
            query = query.where(User.is_active == is_active)
        
        # Apply role filter if specified
        if role:
            # Join with user_roles and roles
            query = query.join(UserRole, User.user_id == UserRole.user_id)
            query = query.join(Role, UserRole.role_id == Role.role_id)
            query = query.where(Role.role_name == role.lower())
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        offset = (page - 1) * limit
        
        # Apply pagination and ordering
        query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
        
        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Build user list with additional info
        user_list = []
        for user in users:
            # Get user roles
            roles = await self._get_user_roles(user.user_id)
            
            # Get upload count
            upload_count = await self._get_user_upload_count(user.user_id)
            
            user_info = UserBasicInfo(
                user_id=user.user_id,
                email=user.email,
                display_name=user.display_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                roles=roles,
                upload_count=upload_count
            )
            user_list.append(user_info)
        
        # Build pagination info
        pagination = PaginationInfo(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
        
        return user_list, pagination
    
    async def get_user_detail(self, user_id: UUID) -> Optional[UserDetailInfo]:
        """
        Get detailed information about a specific user
        
        Args:
            user_id: User UUID
        
        Returns:
            UserDetailInfo or None if not found
        """
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Get user roles
        roles = await self._get_user_roles(user.user_id)
        
        # Get upload count
        upload_count = await self._get_user_upload_count(user.user_id)
        
        user_detail = UserDetailInfo(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=roles,
            upload_count=upload_count,
            last_login=None  # TODO: Add last_login tracking
        )
        
        return user_detail
    
    async def create_user(self, user_data: CreateUserRequest) -> UserDetailInfo:
        # Check if email already exists
        existing_user = await self._get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user
        new_user = User(
            user_id=uuid.uuid4(),
            email=user_data.email,
            display_name=user_data.display_name,
            hashed_password=hashed_password,
            is_active=False,
            is_verified=False
        )
        
        self.db.add(new_user)
        await self.db.flush()
        
        # Assign role
        await self._assign_role_to_user(new_user.user_id, user_data.role)

        # Trigger verification process
        await self._send_verification_email(new_user)
        
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # Return user detail
        return await self.get_user_detail(new_user.user_id)
    
    async def update_user(
        self,
        user_id: UUID,
        user_data: UpdateUserRequest
    ) -> Optional[UserDetailInfo]:
        """
        Update user information
        
        Args:
            user_id: User UUID
            user_data: Update data
        
        Returns:
            Updated user detail or None if not found
        """
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Update fields
        if user_data.display_name is not None:
            user.display_name = user_data.display_name
        
        if user_data.email is not None:
            # Check if new email is already taken by another user
            existing = await self._get_user_by_email(user_data.email)
            if existing and existing.user_id != user_id:
                raise ValueError("Email already in use")
            user.email = user_data.email
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        # Update role if specified
        if user_data.role is not None:
            # Remove existing roles
            await self._remove_all_user_roles(user_id)
            # Assign new role
            await self._assign_role_to_user(user_id, user_data.role)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return await self.get_user_detail(user_id)
    
    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user (soft delete by setting is_active = False)
        
        Args:
            user_id: User UUID
        
        Returns:
            True if deleted, False if not found
        """
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Soft delete
        from datetime import datetime, timezone
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        user.is_active = False
        user.is_deleted = True
        await self.db.commit()
        
        return True
    
    async def update_user_status(self, user_id: UUID, is_active: bool) -> Optional[UserDetailInfo]:
        """
        Update user active status
        
        Args:
            user_id: User UUID
            is_active: New status
        
        Returns:
            Updated user detail or None if not found
        """
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        user.is_active = is_active
        await self.db.commit()
        await self.db.refresh(user)
        
        return await self.get_user_detail(user_id)
    
    async def get_user_stats(self) -> UserStatsResponse:
        """
        Get overall user statistics
        
        Returns:
            User statistics
        """
        # Total users
        total_query = select(func.count(User.user_id)).where(User.is_deleted == False)
        total_result = await self.db.execute(total_query)
        total_users = total_result.scalar() or 0
        
        # Active users
        active_query = select(func.count(User.user_id)).where(User.is_active == True, User.is_deleted == False)
        active_result = await self.db.execute(active_query)
        active_users = active_result.scalar() or 0
        
        # Verified users
        verified_query = select(func.count(User.user_id)).where(User.is_verified == True, User.is_deleted == False)
        verified_result = await self.db.execute(verified_query)
        verified_users = verified_result.scalar() or 0
        
        # Users by role
        role_query = text("""
            SELECT r.role_name,
                   COUNT(DISTINCT CASE WHEN u.is_deleted = false THEN ur.user_id END) as count
            FROM roles r
            LEFT JOIN user_roles ur ON r.role_id = ur.role_id
            LEFT JOIN users u ON ur.user_id = u.user_id
            GROUP BY r.role_name
        """)
        role_result = await self.db.execute(role_query)
        users_by_role = {row[0]: row[1] for row in role_result}
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            users_by_role=users_by_role
        )
    
    # ===================== HELPER METHODS =====================
    
    async def _get_user_roles(self, user_id: UUID) -> List[str]:
        """Get list of role names for a user"""
        query = text("""
            SELECT r.role_name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.role_id
            WHERE ur.user_id = :user_id
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        """)
        result = await self.db.execute(query, {"user_id": str(user_id)})
        return [row[0] for row in result]
    
    async def _get_user_upload_count(self, user_id: UUID) -> int:
        """Get total upload count for a user"""
        # Query from upload_logs table if exists
        query = text("""
            SELECT COUNT(*) 
            FROM upload_logs 
            WHERE user_id = :user_id
        """)
        try:
            result = await self.db.execute(query, {"user_id": str(user_id)})
            count = result.scalar()
            return count or 0
        except:
            # Table might not exist or no uploads
            return 0
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _assign_role_to_user(self, user_id: UUID, role_name: str):
        """Assign a role to user"""
        # Get role by name
        role_query = select(Role).where(Role.role_name == role_name.lower())
        role_result = await self.db.execute(role_query)
        role = role_result.scalar_one_or_none()
        
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        # Create user_role
        user_role = UserRole(
            user_id=user_id,
            role_id=role.role_id,
            assigned_by=None,  # System assigned
            expires_at=None
        )
        self.db.add(user_role)

    async def _send_verification_email(self, user: User) -> None:
        """Generate verification token and send verification email."""
        import logging
        from datetime import datetime, timedelta, timezone
        import os

        logger = logging.getLogger(__name__)

        use_mock_email = os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"
        if use_mock_email:
            from app.utils.mock_email_service import mock_email_service as email_service
            logger.info("Using MOCK email service for admin-created user verification")
        else:
            from app.utils.email_service import email_service
            logger.info("Using REAL email service for admin-created user verification")

        verification_token = email_service.generate_verification_token()

        # Remove existing tokens for this email
        delete_tokens = text("""
            DELETE FROM verification_tokens
            WHERE email = :email AND token_type = 'email_verification'
        """)
        await self.db.execute(delete_tokens, {"email": user.email})

        insert_token = text("""
            INSERT INTO verification_tokens (token_id, email, token, token_type, expires_at, is_used, created_at, updated_at)
            VALUES (:token_id, :email, :token, :token_type, :expires_at, :is_used, :created_at, :updated_at)
        """)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.execute(
            insert_token,
            {
                "token_id": str(uuid.uuid4()),
                "email": user.email,
                "token": verification_token,
                "token_type": "email_verification",
                "expires_at": now + timedelta(hours=24),
                "is_used": False,
                "created_at": now,
                "updated_at": now,
            },
        )

        try:
            await email_service.send_verification_email_async(user.email, verification_token)
            logger.info("Verification email sent to %s", user.email)
        except Exception as exc:  # pragma: no cover - external service call
            logger.error("Failed to send verification email to %s: %s", user.email, exc)
    
    async def _remove_all_user_roles(self, user_id: UUID):
        """Remove all roles from user"""
        query = delete(UserRole).where(UserRole.user_id == user_id)
        await self.db.execute(query)
    
    async def resend_verification_email(self, user_id: UUID) -> bool:
        """
        Resend verification email to unverified user
        
        Args:
            user_id: User UUID
        
        Returns:
            True if email sent successfully, False if user not found or already verified
        """
        # Get user
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Check if already verified
        if user.is_verified:
            return False
        
        # Import email service (same pattern as auth_service)
        import os
        import logging
        logger = logging.getLogger(__name__)
        
        use_mock_email = os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"
        if use_mock_email:
            from app.utils.mock_email_service import mock_email_service as email_service
            logger.info("Using MOCK email service for verification resend")
        else:
            from app.utils.email_service import email_service
            logger.info("Using REAL email service for verification resend")
        
        # Generate new verification token
        verification_token = email_service.generate_verification_token()
        
        # Delete old verification tokens for this user (use email column)
        delete_old_tokens = text("""
            DELETE FROM verification_tokens 
            WHERE email = :email AND token_type = 'email_verification'
        """)
        await self.db.execute(delete_old_tokens, {"email": user.email})

        # Insert new token matching verification_tokens schema
        from datetime import datetime, timedelta, timezone
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        insert_token = text("""
            INSERT INTO verification_tokens (token_id, email, token, token_type, expires_at, is_used, created_at, updated_at)
            VALUES (:token_id, :email, :token, :token_type, :expires_at, :is_used, :created_at, :updated_at)
        """)
        await self.db.execute(insert_token, {
            "token_id": str(uuid.uuid4()),
            "email": user.email,
            "token": verification_token,
            "token_type": "email_verification",
            "expires_at": current_time + timedelta(hours=24),
            "is_used": False,
            "created_at": current_time,
            "updated_at": current_time
        })
        
        await self.db.commit()
        
        # Send verification email
        try:
            await email_service.send_verification_email_async(user.email, verification_token)
            logger.info(f"Verification email resent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
