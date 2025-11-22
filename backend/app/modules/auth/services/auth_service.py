import os
import uuid
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.core.Security.password import hash_password, verify_password
from app.modules.auth.models.roles import Role
from app.modules.auth.models.user import User
from app.modules.profile.models.user_profile import UserProfile
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.verification_token import VerificationToken
from app.modules.auth.schemas.user_schemas import UserCreate
from app.utils.constants.error_codes import (
    AUTH_EMAIL_EXISTS,
    AUTH_PASSWORD_WEAK,
    AUTH_INVALID_CREDENTIALS,
    AUTH_ACCOUNT_INACTIVE,
    AUTH_VERIFICATION_REQUIRED,
    USER_INVALID_DATA,
    USER_NOT_FOUND,
)
from app.utils.validators.auth_validators import (
    validate_password_strength,
    validate_email,
    validate_username,
)

logger = logging.getLogger(__name__)

# Dịch vụ Email (mock/thật)
use_mock_email = (
    os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"
)
if use_mock_email:
    from app.utils.mock_email_service import mock_email_service as email_service

    logger.info("Sử dụng dịch vụ email MOCK")
else:
    from app.utils.email_service import email_service

    logger.info("Sử dụng dịch vụ email THỰC")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =====================================================================
    # GETTERS
    # =====================================================================

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Lấy user theo email (user chưa bị xóa).
        """
        try:
            email_error = validate_email(email)
            if email_error:
                raise Exception(
                    message=f"Định dạng email không hợp lệ: {email_error}",
                    error_code=USER_INVALID_DATA,
                )

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
        except Exception:
            raise
        except Exception as e:
            logger.error(
                "Lỗi khi lấy user theo email %s: %s",
                email,
                str(e),
            )
            raise

    async def get_user_by_username(self, user_name: str) -> Optional[User]:
        """
        Lấy user theo user_name (user chưa bị xóa) kèm roles.
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

            result = await self.db.execute(sql, {"user_name": user_name})
            row = result.mappings().first()

            if not row:
                return None

            user = User.model_validate(dict(row))
            
            # Load user roles separately
            roles_sql = text(
                """
                SELECT r.role_id, r.role_name, r.description, r.is_active, 
                       ur.assigned_at, ur.assigned_by
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.role_id
                WHERE ur.user_id = :user_id
            """
            )
            
            roles_result = await self.db.execute(roles_sql, {"user_id": user.user_id})
            roles_rows = roles_result.mappings().all()
            
            # Attach roles to user
            if roles_rows:
                user_roles = []
                for role_row in roles_rows:
                    role = Role.model_validate(dict(role_row))
                    user_role = UserRole(
                        user_id=user.user_id,
                        role_id=role.role_id,
                        assigned_at=role_row['assigned_at'],
                        assigned_by=role_row['assigned_by']
                    )
                    user_role.role = role
                    user_roles.append(user_role)
                user.user_roles = user_roles

            return user
        except Exception as e:
            logger.error(
                "Lỗi khi lấy user theo username %s: %s",
                user_name,
                str(e),
            )
            raise

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Lấy user theo ID, kèm profile và roles, chỉ user chưa bị xóa.
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

            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.mappings().first()

            if not row:
                return None

            user_data = {
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "is_active": row["is_active"],
                "is_verified": row["is_verified"],
                "is_deleted": row["is_deleted"],
                "token_version": row.get("token_version", 0),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            user = User.model_validate(user_data)

            # Hồ sơ
            if row["profile_created_at"] is not None:
                profile_data = {
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

            # Vai trò
            roles_sql = text(
                """
                SELECT
                    ur.user_id,
                    ur.role_id,
                    ur.assigned_by,
                    ur.assigned_at,
                    ur.expires_at,
                    r.role_id as role_role_id,
                    r.role_name,
                    r.description,
                    r.is_active,
                    r.created_at as role_created_at,
                    r.updated_at as role_updated_at
                FROM user_roles ur
                INNER JOIN roles r ON ur.role_id = r.role_id
                WHERE ur.user_id = :user_id
                  AND r.is_active = true
            """
            )

            roles_result = await self.db.execute(roles_sql, {"user_id": user_id})
            roles_rows = roles_result.mappings().all()

            user_roles = []
            for role_row in roles_rows:
                role = Role(
                    role_id=role_row["role_role_id"],
                    role_name=role_row["role_name"],
                    description=role_row["description"],
                    is_active=role_row["is_active"],
                    created_at=role_row["role_created_at"],
                    updated_at=role_row["role_updated_at"],
                )
                user_role = UserRole(
                    user_id=role_row["user_id"],
                    role_id=role_row["role_id"],
                    assigned_by=role_row["assigned_by"],
                    assigned_at=role_row["assigned_at"],
                    expires_at=role_row["expires_at"],
                )
                user_role.role = role
                user_roles.append(user_role)

            user.user_roles = user_roles

            return user

        except Exception as e:
            logger.error(
                "Lỗi khi lấy user theo ID %s: %s",
                user_id,
                str(e),
            )
            raise

    # =====================================================================
    # CREATE USER
    # =====================================================================

    async def create_user(self, user_data: UserCreate) -> User:
        try:
            # Xác thực email
            email_errors = validate_email(user_data.email)
            if email_errors:
                raise Exception(
                    message=f"Xác thực email thất bại: {email_errors}",
                    error_code=USER_INVALID_DATA,
                )

            # Kiểm tra email trùng lặp
            existing_user_email = await self.get_user_by_email(user_data.email)
            if existing_user_email:
                raise Exception(
                    message="Email đã được đăng ký",
                    error_code=AUTH_EMAIL_EXISTS,
                )

            # Xác thực tên người dùng
            username_error = validate_username(user_data.user_name, user_data.email)
            if username_error:
                raise Exception(
                    message=username_error,
                    error_code=USER_INVALID_DATA,
                )

            # Kiểm tra tên người dùng trùng lặp
            existing_user_username = await self.get_user_by_username(
                user_data.user_name
            )
            if existing_user_username:
                raise Exception(
                    message="Tên người dùng đã được sử dụng",
                    error_code=USER_INVALID_DATA,
                )

            # Xác thực mật khẩu
            password_errors = validate_password_strength(
                user_data.password, 
                username=user_data.user_name, 
                email=user_data.email
            )
            if password_errors:
                raise Exception(
                    message=password_errors,
                    error_code=AUTH_PASSWORD_WEAK,
                )

            user_id = uuid.uuid4()
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            hashed_password = hash_password(user_data.password)

            # Thêm người dùng: schema mới với token_version và is_deleted
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

            # Thêm hồ sơ người dùng
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
                    "full_name": user_data.full_name
                    if hasattr(user_data, "full_name")
                    else None,
                    "gender": user_data.gender
                    if hasattr(user_data, "gender")
                    else None,
                    "created_at": current_time,
                    "updated_at": current_time,
                },
            )

            # Gán role 'user' mặc định nếu có
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
            logger.info(
                "Giao dịch database đã được commit cho user: %s",
                user_data.email,
            )

            # Lấy lại user
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
                raise Exception(
                    message="Không thể lấy lại user đã tạo",
                    error_code=USER_INVALID_DATA,
                )

            user = User.model_validate(dict(user_mapping))
            logger.info(
                "Đã tạo thành công user với email: %s",
                user_data.email,
            )
            return user

        except Exception:
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
                logger.error(
                    "Không thể rollback giao dịch: %s",
                    str(rollback_error),
                )

            raise Exception(
                message="Không thể tạo user do lỗi nội bộ",
                error_code=USER_INVALID_DATA,
            )

    # =====================================================================
    # AUTHENTICATE
    # =====================================================================

    async def authenticate_user(self, user_name: str, password: str) -> User:
        try:
            user = await self.get_user_by_username(user_name)
            if not user:
                raise ValueError("Tên người dùng hoặc mật khẩu không hợp lệ")

            if not user.is_active:
                raise ValueError("Tài khoản đã bị vô hiệu hóa")

            # Nếu hệ thống vẫn muốn đảm bảo account verified:
            if not user.is_verified:
                raise ValueError("Yêu cầu xác minh tài khoản")

            if not verify_password(password, user.hashed_password):
                raise ValueError("Tên người dùng hoặc mật khẩu không hợp lệ")

            # Cập nhật updated_at
            await self.db.execute(
                text(
                    """
                    UPDATE users
                    SET updated_at = :updated_at
                    WHERE user_id = :user_id
                """
                ),
                {
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                    "user_id": user.user_id,
                },
            )
            await self.db.commit()

            # Lấy lại user đầy đủ (có profile, roles)
            updated_user = await self.get_user_by_id(user.user_id)
            if updated_user is None:
                raise ValueError("Không tìm thấy user sau khi xác thực")

            logger.info("User đã xác thực thành công: %s", user_name)
            return updated_user

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn trong quá trình xác thực: %s",
                str(e),
            )
            raise ValueError("Xác thực thất bại do lỗi nội bộ")

    # =====================================================================
    # PASSWORD RESET
    # =====================================================================

    async def initiate_password_reset(self, email: str) -> bool:
        try:
            import random

            user = await self.get_user_by_email(email)
            if not user:
                delay = random.uniform(0.5, 2.0)
                await asyncio.sleep(delay)
                return True

            reset_token = email_service.generate_verification_token()
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)

            # Vô hiệu hóa tất cả token reset password cũ của email này
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

            # Tạo token mới
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

            try:
                asyncio.create_task(
                    email_service.send_password_reset_email_async(
                        email,
                        reset_token,
                    )
                )
                logger.info("Email đặt lại mật khẩu đã được đưa vào hàng đợi cho: %s", email)
            except Exception as e:
                logger.error(
                    "Không thể đưa email đặt lại mật khẩu vào hàng đợi cho %s: %s",
                    email,
                    str(e),
                )

            return True

        except Exception:
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn trong quá trình khởi tạo đặt lại mật khẩu: %s",
                str(e),
            )
            raise Exception(
                message="Khởi tạo đặt lại mật khẩu thất bại do lỗi nội bộ",
                error_code=AUTH_INVALID_CREDENTIALS,
            )

    async def reset_password(
        self,
        email: str,
        token: str,
        new_password: str,
    ) -> bool:
        try:
            password_errors = validate_password_strength(new_password, email=email)
            if password_errors:
                raise Exception(
                    message=password_errors,
                    error_code=AUTH_PASSWORD_WEAK,
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

            result = await self.db.execute(
                token_sql,
                {"email": email, "token": token},
            )
            token_row = result.mappings().first()

            if not token_row:
                raise Exception(
                    message="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn",
                    error_code=AUTH_INVALID_CREDENTIALS,
                )

            verification_token = VerificationToken.model_validate(dict(token_row))

            if verification_token.is_expired:
                raise Exception(
                    message="Token đặt lại mật khẩu đã hết hạn",
                    error_code=AUTH_INVALID_CREDENTIALS,
                )

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
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )

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
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )

            await self.db.commit()
            logger.info("Đặt lại mật khẩu thành công cho user: %s", email)
            return True

        except Exception:
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn trong quá trình đặt lại mật khẩu: %s",
                str(e),
            )
            raise Exception(
                message="Đặt lại mật khẩu thất bại do lỗi nội bộ",
                error_code=AUTH_INVALID_CREDENTIALS,
            )

    # =====================================================================
    # CHANGE PASSWORD
    # =====================================================================

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        try:
            user = await self.get_user_by_id(user_id=user_id)
            if not user:
                raise Exception(
                    message="Không tìm thấy người dùng",
                    error_code=USER_NOT_FOUND,
                )

            password_errors = validate_password_strength(
                new_password, 
                username=user.user_name, 
                email=user.email
            )
            if password_errors:
                raise Exception(
                    message=password_errors,
                    error_code=AUTH_PASSWORD_WEAK,
                )

            if not verify_password(old_password, user.hashed_password):
                raise Exception(
                    message="Mật khẩu hiện tại không đúng",
                    error_code=AUTH_INVALID_CREDENTIALS,
                )

            hashed_password = hash_password(new_password)

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
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )

            await self.db.commit()

            try:
                asyncio.create_task(
                    email_service.send_password_changed_notification_async(
                        user.email,
                        user.user_name or "",
                    )
                )
                logger.info(
                    "Thông báo thay đổi mật khẩu đã được đưa vào hàng đợi cho: %s",
                    user.email,
                )
            except Exception as e:
                logger.error(
                    "Không thể đưa thông báo thay đổi mật khẩu vào hàng đợi cho %s: %s",
                    user.email,
                    str(e),
                )

            logger.info(
                "Mật khẩu đã được thay đổi thành công cho user: %s",
                user_id,
            )
            return True

        except Exception:
            raise
        except Exception as e:
            logger.error(
                "Lỗi không mong muốn trong quá trình thay đổi mật khẩu: %s",
                str(e),
            )
            raise Exception(
                message="Thay đổi mật khẩu thất bại do lỗi nội bộ",
                error_code="PASSWORD_CHANGE_ERROR",
            )

    # =====================================================================
    # TOKEN VERSION (REVOKE ALL TOKENS)
    # =====================================================================

    async def get_user_token_version(self, user_id: uuid.UUID) -> Optional[int]:
        try:
            sql = text(
                """
                SELECT token_version
                FROM users
                WHERE user_id = :user_id
                  AND is_deleted = false
            """
            )

            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.first()

            return row[0] if row else None

        except Exception as e:
            logger.error(
                "Lỗi khi lấy phiên bản token cho user %s: %s",
                user_id,
                str(e),
            )
            raise

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> dict:
        try:
            sql = text(
                """
                UPDATE users
                SET token_version = COALESCE(token_version, 0) + 1,
                    updated_at = :updated_at
                WHERE user_id = :user_id
                  AND is_deleted = false
                RETURNING token_version - 1 AS old_version,
                          token_version     AS new_version
            """
            )

            result = await self.db.execute(
                sql,
                {
                    "user_id": user_id,
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )
            row = result.first()
            await self.db.commit()

            if not row:
                logger.warning(
                    "Không tìm thấy user %s để thu hồi token",
                    user_id,
                )
                return {
                    "success": False,
                    "user_id": str(user_id),
                    "message": "Không tìm thấy user",
                }

            old_version = row[0]
            new_version = row[1]

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
                "message": "Tất cả tokens đã bị thu hồi. User phải đăng nhập lại.",
            }

        except Exception as e:
            logger.error(
                "Lỗi khi thu hồi tất cả tokens cho user %s: %s",
                user_id,
                str(e),
            )
            raise Exception(
                message="Không thể thu hồi tokens",
                error_code="TOKEN_REVOKE_ERROR",
            )
