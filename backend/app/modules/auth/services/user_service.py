import uuid
import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.core.Security.password import hash_password
from app.modules.auth.models.user import User
from app.modules.profile.models.user_profile import UserProfile
from app.modules.auth.schemas.user_schemas import UserCreate
from app.utils.constants.error_codes import USER_INVALID_DATA, AUTH_PASSWORD_WEAK
from app.utils.validators.auth_validators import (
    validate_email,
    validate_username,
    validate_password_strength,
)

# Import helpers
from . import _helpers

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Lấy user theo email (user chưa bị xóa)
        """
        try:
            # Validate email
            _helpers.raise_if_validation_fails(
                validate_email(email),
                USER_INVALID_DATA
            )

            sql = text(
                """
                SELECT *
                FROM users
                WHERE email = :email
                  AND is_deleted = false
            """
            )

            row_dict = await _helpers.execute_query_one(self.db, sql, {"email": email})
            return User.model_validate(row_dict) if row_dict else None

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Lỗi khi lấy user theo email %s: %s", email, str(e))
            raise

    async def get_user_by_username(self, user_name: str) -> Optional[User]:
        """
        Lấy user theo user_name (user chưa bị xóa) kèm roles
        """
        try:
            # Query user
            sql = text(
                """
                SELECT *
                FROM users
                WHERE user_name = :user_name
                  AND is_deleted = false
            """
            )

            row_dict = await _helpers.execute_query_one(self.db, sql, {"user_name": user_name})
            if not row_dict:
                return None

            user = User.model_validate(row_dict)
            
            # Load user roles
            user.user_roles = await _helpers.load_user_roles(self.db, user.user_id)

            return user
        except Exception as e:
            logger.error("Lỗi khi lấy user theo username %s: %s", user_name, str(e))
            raise

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Lấy user theo ID, kèm profile và roles, chỉ user chưa bị xóa
        """
        try:
            sql = text(
                """
                SELECT
                    u.*,
                    p.full_name,
                    p.phone,
                    p.date_of_birth,
                    p.gender,
                    p.address,
                    p.avatar_url,
                    p.created_at as profile_created_at,
                    p.updated_at as profile_updated_at
                FROM users u
                LEFT JOIN user_profiles p ON u.user_id = p.user_id
                WHERE u.user_id = :user_id
                  AND u.is_deleted = false
            """
            )

            row_dict = await _helpers.execute_query_one(self.db, sql, {"user_id": user_id})
            if not row_dict:
                return None

            # Build user object
            user_data = {
                "user_id": row_dict["user_id"],
                "user_name": row_dict["user_name"],
                "email": row_dict["email"],
                "hashed_password": row_dict["hashed_password"],
                "is_active": row_dict["is_active"],
                "is_verified": row_dict["is_verified"],
                "is_deleted": row_dict["is_deleted"],
                "token_version": row_dict.get("token_version", 0),
                "created_at": row_dict["created_at"],
                "updated_at": row_dict["updated_at"],
            }
            user = User.model_validate(user_data)

            # Attach profile if exists
            if row_dict["profile_created_at"] is not None:
                profile_data = {
                    "user_id": row_dict["user_id"],
                    "full_name": row_dict["full_name"],
                    "phone": row_dict["phone"],
                    "date_of_birth": row_dict["date_of_birth"],
                    "gender": row_dict["gender"],
                    "address": row_dict["address"],
                    "avatar_url": row_dict["avatar_url"],
                    "created_at": row_dict["profile_created_at"],
                    "updated_at": row_dict["profile_updated_at"],
                }
                user.profile = UserProfile.model_validate(profile_data)

            # Load roles
            user.user_roles = await _helpers.load_user_roles(self.db, user_id)

            return user

        except Exception as e:
            logger.error("Lỗi khi lấy user theo ID %s: %s", user_id, str(e))
            raise

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Tạo user mới với full validation.
        
        Args:
            user_data: Dữ liệu user để tạo
            
        Returns:
            User object đã được tạo
            
        Raises:
            HTTPException: Nếu validation fail hoặc email/username đã tồn tại
        """
        try:
            # Validate email
            _helpers.raise_if_validation_fails(
                validate_email(user_data.email),
                USER_INVALID_DATA
            )

            # Check duplicate email
            existing_user_email = await self.get_user_by_email(user_data.email)
            if existing_user_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email đã được đăng ký"
                )

            # Validate username
            _helpers.raise_if_validation_fails(
                validate_username(user_data.user_name, user_data.email),
                USER_INVALID_DATA
            )

            # Check duplicate username
            existing_user_username = await self.get_user_by_username(user_data.user_name)
            if existing_user_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tên người dùng đã được sử dụng"
                )

            # Validate password
            _helpers.raise_if_validation_fails(
                validate_password_strength(
                    user_data.password,
                    username=user_data.user_name,
                    email=user_data.email
                ),
                AUTH_PASSWORD_WEAK
            )

            user_id = uuid.uuid4()
            current_time = _helpers.get_current_utc_time()
            hashed_password = hash_password(user_data.password)

            # Insert user
            await self.db.execute(
                text(
                    """
                    INSERT INTO users (
                        user_id,
                        user_name,
                        email,
                        hashed_password,
                        is_active,
                        is_verified,
                        is_deleted,
                        token_version,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :user_id,
                        :user_name,
                        :email,
                        :hashed_password,
                        :is_active,
                        :is_verified,
                        :is_deleted,
                        :token_version,
                        :created_at,
                        :updated_at
                    )
                """
                ),
                {
                    "user_id": user_id,
                    "user_name": user_data.user_name,
                    "email": user_data.email,
                    "hashed_password": hashed_password,
                    "is_active": True,
                    "is_verified": True,
                    "is_deleted": False,
                    "token_version": 0,
                    "created_at": current_time,
                    "updated_at": current_time,
                },
            )

            # Insert user profile
            await self.db.execute(
                text(
                    """
                    INSERT INTO user_profiles (
                        user_id,
                        full_name,
                        gender,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :user_id,
                        :full_name,
                        :gender,
                        :created_at,
                        :updated_at
                    )
                """
                ),
                {
                    "user_id": user_id,
                    "full_name": user_data.full_name if hasattr(user_data, "full_name") else None,
                    "gender": user_data.gender if hasattr(user_data, "gender") else None,
                    "created_at": current_time,
                    "updated_at": current_time,
                },
            )

            # Assign default 'user' role
            role_result = await self.db.execute(
                text(
                    """
                    SELECT role_id
                    FROM roles
                    WHERE role_name = 'user'
                      AND is_active = true
                """
                )
            )
            role_row = role_result.mappings().first()
            if role_row:
                await self.db.execute(
                    text(
                        """
                        INSERT INTO user_roles (user_id, role_id, assigned_at)
                        VALUES (:user_id, :role_id, :assigned_at)
                    """
                    ),
                    {
                        "user_id": user_id,
                        "role_id": role_row["role_id"],
                        "assigned_at": current_time,
                    },
                )

            await self.db.commit()
            logger.info("Giao dịch database đã được commit cho user: %s", user_data.email)

            # Retrieve created user
            user_result = await self.db.execute(
                text(
                    """
                    SELECT
                        user_id,
                        user_name,
                        email,
                        hashed_password,
                        is_active,
                        is_verified,
                        is_deleted,
                        token_version,
                        created_at,
                        updated_at
                    FROM users
                    WHERE user_id = :user_id
                """
                ),
                {"user_id": user_id},
            )
            user_mapping = user_result.mappings().first()
            if not user_mapping:
                logger.error("Không tìm thấy user sau khi tạo: %s", user_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không thể lấy lại user đã tạo"
                )

            user = User.model_validate(dict(user_mapping))
            logger.info("Đã tạo thành công user với email: %s", user_data.email)
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn khi tạo user %s: %s",
                user_data.email,
                str(e),
                exc_info=True,
            )
            try:
                await self.db.rollback()
                logger.info("Giao dịch đã được rollback do lỗi")
            except Exception as rollback_error:
                logger.error("Không thể rollback giao dịch: %s", str(rollback_error))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tạo user do lỗi nội bộ"
            )
