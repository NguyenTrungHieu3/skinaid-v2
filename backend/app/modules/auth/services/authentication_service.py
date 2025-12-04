import uuid
import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.core.Security.password import verify_password
from app.modules.auth.models.user import User

# Import helpers and user service
from . import _helpers
from .user_service import UserService

logger = logging.getLogger(__name__)


class AuthenticationService:
    def __init__(self, db: AsyncSession, user_service: Optional[UserService] = None):
        self.db = db
        self.user_service = user_service or UserService(db)

    async def authenticate_user(self, user_name: str, password: str) -> User:
        """
        Xác thực user với username và password
        """
        try:
            user = await self.user_service.get_user_by_username(user_name)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tên người dùng hoặc mật khẩu không hợp lệ"
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tài khoản đã bị vô hiệu hóa"
                )

            if not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Yêu cầu xác minh tài khoản"
                )

            if not verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tên người dùng hoặc mật khẩu không hợp lệ"
                )

            # Update last activity time
            await self.db.execute(
                text(
                    """
                    UPDATE users
                    SET updated_at = :updated_at
                    WHERE user_id = :user_id
                """
                ),
                {
                    "updated_at": _helpers.get_current_utc_time(),
                    "user_id": user.user_id,
                },
            )
            await self.db.commit()

            # Reload user with full details
            updated_user = await self.user_service.get_user_by_id(user.user_id)
            if updated_user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không tìm thấy user sau khi xác thực"
                )

            logger.info("User đã xác thực thành công: %s", user_name)
            return updated_user

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Lỗi không mong muốn trong quá trình xác thực: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Xác thực thất bại do lỗi nội bộ"
            )

    async def get_user_token_version(self, user_id: uuid.UUID) -> Optional[int]:
        """
        Lấy token version hiện tại của user
        """
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
        """
        Thu hồi tất cả tokens của user bằng cách tăng token_version
        """
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
                    "updated_at": _helpers.get_current_utc_time(),
                },
            )
            row = result.first()
            await self.db.commit()

            if not row:
                logger.warning("Không tìm thấy user %s để thu hồi token", user_id)
                return {
                    "success": False,
                    "user_id": str(user_id),
                    "message": "Không tìm thấy người dùng",
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
                "message": "Tất cả token đã bị thu hồi. Người dùng phải đăng nhập lại.",
            }

        except Exception as e:
            logger.error("Lỗi khi thu hồi tất cả tokens cho user %s: %s", user_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể thu hồi token"
            )
