from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, UUID
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

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Lấy thông tin user theo ID kèm profile
        """
        try:
            sql = text("""
                SELECT
                    u.*,
                    p.profile_id,
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
            """)

            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.mappings().first()

            if not row:
                return None

            # Create user object
            user_data = {
                "user_id": row["user_id"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "is_active": row["is_active"],
                "is_verified": row["is_verified"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
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
                    "updated_at": row["profile_updated_at"]
                }
                user.profile = UserProfile.model_validate(profile_data)

            return user

        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Lấy thông tin user theo email
        """
        try:
            sql = text("""
                SELECT * FROM users WHERE email = :email
            """)

            result = await self.db.execute(sql, {"email": email})
            row = result.mappings().first()

            if not row:
                return None

            return User.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        is_verified: bool = False
    ) -> User:
        """
        Tạo mới một user
        """
        try:
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            user_id = uuid.uuid4()

            sql = text("""
                INSERT INTO users (user_id, email, hashed_password, is_active, is_verified, created_at, updated_at)
                VALUES (:user_id, :email, :hashed_password, :is_active, :is_verified, :created_at, :updated_at)
                RETURNING *
            """)

            params = {
                "user_id": user_id,
                "email": email,
                "hashed_password": hashed_password,
                "is_active": is_active,
                "is_verified": is_verified,
                "created_at": current_time,
                "updated_at": current_time
            }

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                raise Exception("Failed to get returning row after insert.")

            await self.db.commit()
            return User.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            await self.db.rollback()
            raise

    async def update_user_status(
        self,
        user_id: uuid.UUID,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> Optional[User]:
        """
        Cập nhật trạng thái user
        """
        try:
            update_fields = []
            params = {"user_id": user_id}

            if is_active is not None:
                update_fields.append("is_active = :is_active")
                params["is_active"] = is_active

            if is_verified is not None:
                update_fields.append("is_verified = :is_verified")
                params["is_verified"] = is_verified

            if not update_fields:
                return await self.get_user_by_id(user_id)

            update_fields.append("updated_at = :updated_at")
            params["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

            sql = text(f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE user_id = :user_id
                RETURNING *
            """)

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                return None

            await self.db.commit()
            return User.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to update user status for {user_id}: {e}")
            await self.db.rollback()
            return None

    async def update_user_password(self, user_id: uuid.UUID, hashed_password: str) -> bool:
        """
        Cập nhật mật khẩu user
        """
        try:
            sql = text("""
                UPDATE users
                SET hashed_password = :hashed_password, updated_at = :updated_at
                WHERE user_id = :user_id
            """)

            result = await self.db.execute(sql, {
                "user_id": user_id,
                "hashed_password": hashed_password,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            await self.db.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to update user password for {user_id}: {e}")
            await self.db.rollback()
            return False

    async def get_users_by_status(
        self,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """
        Lấy danh sách users theo trạng thái
        """
        try:
            where_conditions = []
            params = {"limit": limit, "offset": offset}

            if is_active is not None:
                where_conditions.append("is_active = :is_active")
                params["is_active"] = is_active

            if is_verified is not None:
                where_conditions.append("is_verified = :is_verified")
                params["is_verified"] = is_verified

            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            sql = text(f"""
                SELECT * FROM users
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(sql, params)
            rows = result.mappings().all()

            return [User.model_validate(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get users by status: {e}")
            return []

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Xóa user (soft delete bằng cách set is_active = False)
        """
        try:
            sql = text("""
                UPDATE users
                SET is_active = false, updated_at = :updated_at
                WHERE user_id = :user_id AND is_active = true
            """)

            result = await self.db.execute(sql, {
                "user_id": user_id,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            await self.db.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê tổng quan về users
        """
        try:
            total_sql = text("SELECT COUNT(*) as total FROM users")
            total_result = await self.db.execute(total_sql)
            total_row = total_result.mappings().first()
            total_users = total_row["total"] if total_row else 0

            active_sql = text("SELECT COUNT(*) as active FROM users WHERE is_active = true")
            active_result = await self.db.execute(active_sql)
            active_row = active_result.mappings().first()
            active_users = active_row["active"] if active_row else 0

            verified_sql = text("SELECT COUNT(*) as verified FROM users WHERE is_verified = true")
            verified_result = await self.db.execute(verified_sql)
            verified_row = verified_result.mappings().first()
            verified_users = verified_row["verified"] if verified_row else 0

            inactive_users = total_users - active_users

            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "verified_users": verified_users,
                "unverified_users": active_users - verified_users,
                "verification_rate": (verified_users / active_users * 100) if active_users > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "inactive_users": 0,
                "verified_users": 0,
                "unverified_users": 0,
                "verification_rate": 0
            }