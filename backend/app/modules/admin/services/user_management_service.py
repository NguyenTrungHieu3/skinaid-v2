from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text, delete
from sqlalchemy.orm import selectinload
from sqlmodel import col
from typing import Optional, List, Tuple
from uuid import UUID
import uuid
import logging
from datetime import datetime

from app.modules.auth.models.user import User
from app.modules.profile.models.user_profile import UserProfile
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

logger = logging.getLogger(__name__)


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
        # Xây dựng truy vấn cơ bản
        query = select(User).where(User.is_deleted == False)
        
        # Áp dụng bộ lọc tìm kiếm
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.user_name.ilike(search_pattern)
                )
            )
        
        # Áp dụng bộ lọc trạng thái
        if status:
            is_active = status.lower() == 'active'
            query = query.where(User.is_active == is_active)
        
        # Áp dụng bộ lọc vai trò nếu được chỉ định
        if role:
            # Kết nối với user_roles và roles
            query = query.join(UserRole, User.user_id == UserRole.user_id)
            query = query.join(Role, UserRole.role_id == Role.role_id)
            query = query.where(Role.role_name == role.lower())
        
        # Lấy tổng số
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Tính toán phân trang
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        offset = (page - 1) * limit
        
        # Áp dụng phân trang và sắp xếp
        query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
        
        # Tải profile người dùng sắn và roles
        query = query.options(
            selectinload(User.profile),
            selectinload(User.user_roles).selectinload(UserRole.role)
        )
        
        # Thực thi truy vấn
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Xây dựng danh sách người dùng với thông tin bổ sung
        user_list = []
        for user in users:
            # Lấy vai trò người dùng từ eager loaded data
            roles = []
            if user.user_roles:
                for ur in user.user_roles:
                    if ur.role and (not ur.expires_at or ur.expires_at > datetime.now()):
                        roles.append(ur.role.role_name)
            
            # Lấy số lượng upload
            upload_count = await self._get_user_upload_count(user.user_id)
            
            # Lấy display_name từ profile nếu có, nếu không dùng user_name
            display_name = None
            if hasattr(user, 'profile') and user.profile:
                display_name = user.profile.full_name
            if not display_name:
                display_name = user.user_name
            
            user_info = UserBasicInfo(
                user_id=user.user_id,
                email=user.email,
                display_name=display_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                roles=roles,
                upload_count=upload_count
            )
            user_list.append(user_info)
        
        # Xây dựng thông tin phân trang
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
        query = query.options(
            selectinload(User.profile),
            selectinload(User.user_roles).selectinload(UserRole.role)
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Lấy vai trò người dùng từ eager loaded data
        roles = []
        if user.user_roles:
            for ur in user.user_roles:
                if ur.role and (not ur.expires_at or ur.expires_at > datetime.now()):
                    roles.append(ur.role.role_name)
        
        # Lấy số lượng upload
        upload_count = await self._get_user_upload_count(user.user_id)
        
        # Lấy display_name từ profile nếu có, nếu không dùng user_name
        display_name = None
        if hasattr(user, 'profile') and user.profile:
            display_name = user.profile.full_name
        if not display_name:
            display_name = user.user_name
        
        user_detail = UserDetailInfo(
            user_id=user.user_id,
            email=user.email,
            display_name=display_name,
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
        """
        Create a new user with proper transaction handling
        
        Args:
            user_data: User creation data
        
        Returns:
            UserDetailInfo of the created user
            
        Raises:
            ValueError: If email already exists or role not found or other validation errors
        """
        logger.info(f"Starting create_user for {user_data.email}")
        try:
            # Ensure clean session state
            await self.db.rollback() 
            
            # Kiểm tra email đã tồn tại chưa
            existing_user = await self._get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("Email already registered")
            
            # Xác thực tên hiển thị
            if not user_data.display_name or len(user_data.display_name.strip()) < 2:
                raise ValueError("Display name must be at least 2 characters")
            
            if len(user_data.display_name) > 100:
                raise ValueError("Display name must not exceed 100 characters")
            
            # Xác thực mật khẩu
            if len(user_data.password) < 6:
                raise ValueError("Password must be at least 6 characters")
            
            # Tạo username từ email (phần trước @)
            user_name = user_data.email.split('@')[0]
            # Kiểm tra username đã tồn tại, nếu có thì thêm hậu tố ngẫu nhiên
            existing_username = await self._get_user_by_username(user_name)
            if existing_username:
                user_name = f"{user_name}_{uuid.uuid4().hex[:6]}"
            
            # Mã hóa mật khẩu
            hashed_password = hash_password(user_data.password)
            
            # Tạo người dùng
            new_user_id = uuid.uuid4()
            new_user = User(
                user_id=new_user_id,
                user_name=user_name,
                email=user_data.email,
                hashed_password=hashed_password,
                is_active=True,  # Admin-created users are active by default
                is_verified=True  # Admin-created users are verified by default
            )
            
            self.db.add(new_user)
            await self.db.flush()  # Flush to get user_id for profile and role assignment
            
            # Tạo profile người dùng với display_name
            new_profile = UserProfile(
                user_id=new_user_id,
                full_name=user_data.display_name.strip()
            )
            self.db.add(new_profile)
            await self.db.flush()
            
            # Gán vai trò (có thể gây ra ValueError nếu không tìm thấy vai trò)
            await self._assign_role_to_user(new_user.user_id, user_data.role)
            
            # Commit giao dịch (user + profile + gán vai trò)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            logger.info(f"User created successfully: {new_user.email} (ID: {new_user.user_id})")
            
            # Gửi email xác thực SAU khi commit (hoạt động không quan trọng)
            # Nếu email thất bại, người dùng vẫn được tạo thành công
            try:
                await self._send_verification_email(new_user)
                logger.info(f"Verification email sent to {new_user.email}")
            except Exception as email_error:
                logger.warning(f"Failed to send verification email to {new_user.email}: {email_error}")
                # Không raise - lỗi email không nên làm thất bại việc tạo người dùng
            
            # Trả về chi tiết người dùng
            user_detail = await self.get_user_detail(new_user.user_id)
            if not user_detail:
                logger.error(f"Failed to retrieve created user detail: {new_user.user_id}")
                raise ValueError("User created but failed to retrieve details")
            
            return user_detail
            
        except ValueError:
            # Raise lại lỗi xác thực
            await self.db.rollback()
            raise
        except Exception as e:
            # Rollback khi có lỗi để ngăn dữ liệu bị thiếu
            await self.db.rollback()
            logger.error(f"Failed to create user {user_data.email}: {e}")
            raise ValueError(f"Failed to create user: {str(e)}")
    
    async def update_user(
        self,
        user_id: UUID,
        user_data: UpdateUserRequest
    ) -> Optional[UserDetailInfo]:
        """
        Update user information with proper transaction handling
        
        Args:
            user_id: User UUID
            user_data: Update data
        
        Returns:
            Updated user detail or None if not found
            
        Raises:
            ValueError: If validation fails or email already in use
        """
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        query = query.options(selectinload(User.profile))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        try:
            # Xác thực và cập nhật display_name (full_name trong profile) nếu được cung cấp
            if user_data.display_name is not None:
                if len(user_data.display_name.strip()) < 2:
                    raise ValueError("Display name must be at least 2 characters")
                if len(user_data.display_name) > 100:
                    raise ValueError("Display name must not exceed 100 characters")
                
                # Cập nhật hoặc tạo profile
                if hasattr(user, 'profile') and user.profile:
                    user.profile.full_name = user_data.display_name.strip()
                else:
                    # Tạo profile nếu chưa tồn tại
                    new_profile = UserProfile(
                        user_id=user_id,
                        full_name=user_data.display_name.strip()
                    )
                    self.db.add(new_profile)
            
            # Xác thực và cập nhật email nếu được cung cấp
            if user_data.email is not None:
                # Kiểm tra email mới đã được người dùng khác sử dụng chưa
                existing = await self._get_user_by_email(user_data.email)
                if existing and existing.user_id != user_id:
                    raise ValueError("Email already in use")
                user.email = user_data.email
            
            # Cập nhật trạng thái hoạt động nếu được cung cấp
            if user_data.is_active is not None:
                user.is_active = user_data.is_active
            
            # Cập nhật vai trò nếu được chỉ định
            if user_data.role is not None:
                # Xóa các vai trò hiện tại
                await self._remove_all_user_roles(user_id)
                # Gán vai trò mới (có thể gây ra ValueError nếu không tìm thấy vai trò)
                await self._assign_role_to_user(user_id, user_data.role)
            
            # Commit tất cả thay đổi
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User updated successfully: {user.email} (ID: {user_id})")
            
            return await self.get_user_detail(user_id)
            
        except ValueError:
            # Raise lại lỗi xác thực sau khi rollback
            await self.db.rollback()
            raise
        except Exception as e:
            # Rollback khi có lỗi
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise ValueError(f"Failed to update user: {str(e)}")
    
    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user (soft delete by setting is_deleted = True)
        
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
        
        try:
            # Xóa mềm
            from datetime import datetime, timezone
            user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            user.is_active = False
            user.is_deleted = True
            
            await self.db.commit()
            
            logger.info(f"User soft deleted: {user.email} (ID: {user_id})")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise ValueError(f"Failed to delete user: {str(e)}")
    
    async def update_user_status(self, user_id: UUID, is_active: bool) -> Optional[UserDetailInfo]:
        """
        Update user active status with transaction handling
        
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
        
        try:
            user.is_active = is_active
            await self.db.commit()
            await self.db.refresh(user)
            
            status_text = "activated" if is_active else "deactivated"
            logger.info(f"User {status_text}: {user.email} (ID: {user_id})")
            
            return await self.get_user_detail(user_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user status {user_id}: {e}")
            raise ValueError(f"Failed to update user status: {str(e)}")
    
    async def get_user_stats(self) -> UserStatsResponse:
        """
        Get overall user statistics
        
        Returns:
            User statistics
        """
        # Tổng số người dùng
        total_query = select(func.count(User.user_id)).where(User.is_deleted == False)
        total_result = await self.db.execute(total_query)
        total_users = total_result.scalar() or 0
        
        # Người dùng đang hoạt động
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
        """Get total upload count for a user from wound_analyses table"""
        query = text("""
            SELECT COUNT(*) 
            FROM wound_analyses 
            WHERE user_id = :user_id 
            AND is_deleted = FALSE
        """)
        try:
            result = await self.db.execute(query, {"user_id": str(user_id)})
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.warning(f"Failed to get upload count for user {user_id}: {e}")
            return 0
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_user_by_username(self, user_name: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.user_name == user_name)
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
        await self.db.commit()

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
        Resend verification email to unverified user with transaction handling
        
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
            logger.info(f"User {user.email} is already verified")
            return False
        
        # Import email service (same pattern as auth_service)
        import os
        
        use_mock_email = os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"
        if use_mock_email:
            from app.utils.mock_email_service import mock_email_service as email_service
            logger.info("Using MOCK email service for verification resend")
        else:
            from app.utils.email_service import email_service
            logger.info("Using REAL email service for verification resend")
        
        try:
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
            
            # Commit token changes
            await self.db.commit()
            
            # Send verification email (after commit, non-critical)
            try:
                await email_service.send_verification_email_async(user.email, verification_token)
                logger.info(f"Verification email resent to {user.email}")
                return True
            except Exception as email_error:
                logger.error(f"Failed to send verification email to {user.email}: {str(email_error)}")
                # Token is created but email failed - still return False
                return False
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create verification token for {user.email}: {str(e)}")
            return False
