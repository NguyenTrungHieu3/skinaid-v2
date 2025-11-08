from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import uuid
from datetime import datetime, timezone

from app.modules.auth.models.user import User
from app.modules.auth.models.user_profile import UserProfile
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_NOT_FOUND, USER_INVALID_DATA

logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ======================== GETTERS ========================

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Lấy thông tin user theo ID kèm profile
        Chỉ lấy user chưa bị xóa (is_deleted = false)
        """
        try:
            sql = text(
                """
                SELECT
                    u.*,
                    p.profile_id,
                    p.full_name,
                    p.phone,
                    p.date_of_birth,
                    p.gender,
                    p.address,
                    p.avatar_url,
                    p.created_at AS profile_created_at,
                    p.updated_at AS profile_updated_at
                FROM users u
                LEFT JOIN user_profiles p ON u.user_id = p.user_id
                WHERE u.user_id = :user_id
                  AND u.is_deleted = false
                """
            )
            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.mappings().first()

            if not row:
                return None

            user_data = {
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "token_version": row.get("token_version", 0),
                "is_active": row["is_active"],
                "is_verified": row["is_verified"],
                "is_deleted": row["is_deleted"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            user = User.model_validate(user_data)

            if row["profile_id"]:
                profile_data = {
                    "profile_id": row["profile_id"],
                    "user_id": row["user_id"],
                    "full_name": row["full_name"],
                    "phone": row["phone"],
                    "date_of_birth": row["date_of_birth"],
                    "gender": row["gender"],
                    "address": row["address"],
                    "avatar_url": row["avatar_url"],
                    "created_at": row["profile_created_at"],
                    "updated_at": row["profile_updated_at"],
                }
                user.profile = UserProfile.model_validate(profile_data)

            return user

        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}", exc_info=True)
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Lấy thông tin user theo email.
        Chỉ lấy user chưa bị xóa (is_deleted = false)
        """
        try:
            sql = text(
                """
                SELECT *
                FROM users
                WHERE email = :email
                  AND is_deleted = false
                """
            )
            result = await self.db.execute(sql, {"email": email})
            row = result.mappings().first()

            if not row:
                return None

            return User.model_validate(dict(row))
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}", exc_info=True)
            return None

    async def get_user_by_username(self, user_name: str) -> Optional[User]:
        """
        Lấy thông tin user theo user_name.
        Chỉ lấy user chưa bị xóa (is_deleted = false)
        """
        try:
            sql = text(
                """
                SELECT *
                FROM users
                WHERE user_name = :user_name
                  AND is_deleted = false
                """
            )
            result = await self.db.execute(sql, {"user_name": user_name})
            row = result.mappings().first()

            if not row:
                return None

            return User.model_validate(dict(row))
        except Exception as e:
            logger.error(
                f"Failed to get user by username {user_name}: {e}", exc_info=True
            )
            return None

    # ======================== CREATE ========================

    async def create_user(
        self,
        user_name: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        is_verified: bool = False,
    ) -> User:
        """
        Tạo mới một user theo schema chuẩn.
        Không sử dụng display_name. Luôn set is_deleted = false khi tạo.
        """
        try:
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            user_id = uuid.uuid4()

            sql = text(
                """
                INSERT INTO users (
                    user_id,
                    user_name,
                    email,
                    hashed_password,
                    token_version,
                    is_active,
                    is_verified,
                    is_deleted,
                    created_at,
                    updated_at
                )
                VALUES (
                    :user_id,
                    :user_name,
                    :email,
                    :hashed_password,
                    :token_version,
                    :is_active,
                    :is_verified,
                    :is_deleted,
                    :created_at,
                    :updated_at
                )
                RETURNING *
                """
            )

            params = {
                "user_id": user_id,
                "user_name": user_name,
                "email": email,
                "hashed_password": hashed_password,
                "token_version": 0,
                "is_active": is_active,
                "is_verified": is_verified,
                "is_deleted": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                raise AppBaseException(
                    message="Failed to create user (no returning row)",
                    error_code=USER_INVALID_DATA,
                )

            await self.db.commit()
            return User.model_validate(dict(row))

        except AppBaseException:
            await self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}", exc_info=True)
            await self.db.rollback()
            raise AppBaseException(
                message="Failed to create user",
                error_code=USER_INVALID_DATA,
            )

    # ======================== UPDATE STATUS ========================

    async def update_user_status(
        self,
        user_id: uuid.UUID,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
    ) -> Optional[User]:
        """
        Cập nhật trạng thái user:
        - is_active
        - is_verified
        - is_deleted (soft delete)
        """
        try:
            update_fields: List[str] = []
            params: Dict[str, Any] = {"user_id": user_id}

            if is_active is not None:
                update_fields.append("is_active = :is_active")
                params["is_active"] = is_active

            if is_verified is not None:
                update_fields.append("is_verified = :is_verified")
                params["is_verified"] = is_verified

            if is_deleted is not None:
                update_fields.append("is_deleted = :is_deleted")
                params["is_deleted"] = is_deleted

            if not update_fields:
                # Không có gì để update => trả về user hiện tại (nếu tồn tại)
                return await self.get_user_by_id(user_id)

            update_fields.append("updated_at = :updated_at")
            params["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

            sql = text(
                f"""
                UPDATE users
                SET {", ".join(update_fields)}
                WHERE user_id = :user_id
                RETURNING *
                """
            )

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                await self.db.commit()
                return None

            await self.db.commit()
            return User.model_validate(dict(row))

        except Exception as e:
            logger.error(
                f"Failed to update user status for {user_id}: {e}", exc_info=True
            )
            await self.db.rollback()
            return None

    # ======================== UPDATE PASSWORD ========================

    async def update_user_password(
        self,
        user_id: uuid.UUID,
        hashed_password: str,
    ) -> bool:
        """
        Cập nhật mật khẩu user.
        Chỉ áp dụng cho user chưa bị xóa (is_deleted = false).
        """
        try:
            sql = text(
                """
                UPDATE users
                SET hashed_password = :hashed_password,
                    updated_at = :updated_at
                WHERE user_id = :user_id
                  AND is_deleted = false
                """
            )

            await self.db.execute(
                sql,
                {
                    "user_id": user_id,
                    "hashed_password": hashed_password,
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )
            await self.db.commit()
            return True

        except Exception as e:
            logger.error(
                f"Failed to update password for user {user_id}: {e}", exc_info=True
            )
            await self.db.rollback()
            return False

    # ======================== SOFT DELETE ========================

    async def soft_delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Đánh dấu xóa mềm user (is_deleted = true, is_active = false).
        """
        try:
            sql = text(
                """
                UPDATE users
                SET is_deleted = true,
                    is_active = false,
                    updated_at = :updated_at
                WHERE user_id = :user_id
                """
            )
            result = await self.db.execute(
                sql,
                {
                    "user_id": user_id,
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(
                f"Failed to soft delete user {user_id}: {e}", exc_info=True
            )
            await self.db.rollback()
            return False