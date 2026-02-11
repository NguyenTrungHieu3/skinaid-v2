"""
TokenRepository — Truy vấn database cho Token entities.

Quản lý: VerificationToken, TokenFamily, TokenBlacklist.
Thay thế raw SQL trong TokenFamilyService, PasswordService, TokenCleanupService.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models.token_blacklist import TokenBlacklist
from app.modules.auth.models.token_family import TokenFamily
from app.modules.auth.models.verification_token import VerificationToken

logger = logging.getLogger(__name__)


class TokenRepository:
    """Repository cho Token entities — verification, family, blacklist."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── VERIFICATION TOKEN ────────────────────────────────

    async def create_verification_token(
        self,
        token: VerificationToken,
    ) -> VerificationToken:
        """Lưu verification token mới."""
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def get_valid_verification_token(
        self,
        email: str,
        token: str,
        token_type: str,
    ) -> Optional[VerificationToken]:
        """
        Lấy verification token hợp lệ (chưa dùng + chưa hết hạn).

        Args:
            email: Email liên kết với token
            token: Chuỗi token
            token_type: Loại token (email_verification, password_reset)
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = select(VerificationToken).where(
            VerificationToken.email == email,
            VerificationToken.token == token,
            VerificationToken.token_type == token_type,
            VerificationToken.is_used == False,  # noqa: E712
            VerificationToken.expires_at > now,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def mark_token_used(self, token_id: uuid.UUID) -> None:
        """Đánh dấu verification token đã sử dụng."""
        statement = select(VerificationToken).where(
            VerificationToken.token_id == token_id,
        )
        result = await self.db.execute(statement)
        token_entity = result.scalar_one_or_none()
        if token_entity:
            token_entity.is_used = True
            token_entity.updated_at = datetime.now(timezone.utc).replace(
                tzinfo=None
            )
            await self.db.flush()

    async def invalidate_previous_tokens(
        self,
        email: str,
        token_type: str,
    ) -> int:
        """
        Vô hiệu hóa tất cả token cũ chưa dùng của email cho 1 loại token.

        Returns:
            Số token đã vô hiệu hóa
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = select(VerificationToken).where(
            VerificationToken.email == email,
            VerificationToken.token_type == token_type,
            VerificationToken.is_used == False,  # noqa: E712
        )
        result = await self.db.execute(statement)
        tokens = result.scalars().all()

        count = 0
        for token_entity in tokens:
            token_entity.is_used = True
            token_entity.updated_at = now
            count += 1

        if count > 0:
            await self.db.flush()
        if count > 0:
            await self.db.flush()
        return count

    async def delete_tokens_by_email(
        self,
        email: str,
        token_type: Optional[str] = None
    ) -> int:
        """
        Xóa token của email (Hard delete).

        Args:
            email: Email cần xóa token
            token_type: Loại token (Optional). Nếu None sẽ xóa tất cả.
        """
        stmt = delete(VerificationToken).where(
            VerificationToken.email == email)
        if token_type:
            stmt = stmt.where(VerificationToken.token_type == token_type)

        result = await self.db.execute(stmt)
        # await self.db.flush() # Caller should commit/flush
        return result.rowcount

    # ── TOKEN FAMILY ──────────────────────────────────────

    async def create_token_family(
        self,
        *,
        user_id: uuid.UUID,
        refresh_jti: str,
        access_jti: Optional[str] = None,
        expires_at: datetime,
        parent_jti: Optional[str] = None,
    ) -> TokenFamily:
        """Tạo bản ghi token family."""
        # Chuẩn hóa múi giờ
        if expires_at.tzinfo is not None:
            expires_at = expires_at.astimezone(timezone.utc).replace(
                tzinfo=None
            )

        family = TokenFamily(
            user_id=user_id,
            refresh_token_jti=refresh_jti,
            access_token_jti=access_jti,
            parent_jti=parent_jti,
            expires_at=expires_at,
        )
        self.db.add(family)
        await self.db.flush()
        return family

    async def is_family_revoked(self, refresh_jti: str) -> bool:
        """Kiểm tra token family có bị revoked không."""
        statement = select(TokenFamily.is_revoked).where(
            TokenFamily.refresh_token_jti == refresh_jti,
        )
        result = await self.db.execute(statement)
        row = result.scalar_one_or_none()
        return bool(row) if row is not None else False

    async def get_family_by_jti(self, jti: str) -> Optional[TokenFamily]:
        """Lấy token family theo refresh_jti hoặc access_jti."""
        statement = select(TokenFamily).where(
            (TokenFamily.refresh_token_jti == jti)
            | (TokenFamily.access_token_jti == jti),
            TokenFamily.is_revoked == False,  # noqa: E712
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_family(self, jti: str) -> int:
        """
        Thu hồi token family và thêm tokens vào blacklist.

        Returns:
            Số token đã thêm vào blacklist
        """
        family = await self.get_family_by_jti(jti)
        if not family:
            logger.warning("Không tìm thấy token family: jti=%s", jti)
            return 0

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Thu hồi các token (refresh + access)
        jtis_to_revoke = [
            (family.refresh_token_jti, "refresh"),
        ]
        if family.access_token_jti:
            jtis_to_revoke.append((family.access_token_jti, "access"))

        expires_at = family.expires_at
        if expires_at and expires_at.tzinfo is not None:
            expires_at = expires_at.astimezone(timezone.utc).replace(
                tzinfo=None
            )

        for token_jti, token_type in jtis_to_revoke:
            # Kiểm tra trùng lặp trước khi thêm
            existing = await self.db.execute(
                select(TokenBlacklist).where(TokenBlacklist.jti == token_jti)
            )
            if existing.scalar_one_or_none() is None:
                blacklist_entry = TokenBlacklist(
                    jti=token_jti,
                    token_type=token_type,
                    revoked_at=now,
                    expires_at=expires_at,
                )
                self.db.add(blacklist_entry)

        # Đánh dấu family đã revoked
        family.is_revoked = True
        await self.db.flush()

        logger.info(
            "Đã thu hồi token family: %d tokens", len(jtis_to_revoke)
        )
        return len(jtis_to_revoke)

    async def revoke_entire_chain(self, refresh_jti: str) -> int:
        """
        Thu hồi toàn bộ token chain (phát hiện token reuse).

        Sử dụng parent_jti để tìm chain families liên quan.
        """
        # Tìm tất cả families trong chain qua parent_jti
        chain_jtis: list[str] = []
        current_jti = refresh_jti

        # Duyệt ngược lên chain qua parent_jti
        while current_jti:
            chain_jtis.append(current_jti)
            statement = select(TokenFamily.parent_jti).where(
                TokenFamily.refresh_token_jti == current_jti,
            )
            result = await self.db.execute(statement)
            parent = result.scalar_one_or_none()
            current_jti = parent

        # Duyệt xuôi xuống chain (children)
        children_to_check = [refresh_jti]
        while children_to_check:
            parent_jti = children_to_check.pop(0)
            statement = select(TokenFamily.refresh_token_jti).where(
                TokenFamily.parent_jti == parent_jti,
            )
            result = await self.db.execute(statement)
            children = result.scalars().all()
            for child_jti in children:
                if child_jti not in chain_jtis:
                    chain_jtis.append(child_jti)
                    children_to_check.append(child_jti)

        total_revoked = 0
        for chain_jti in chain_jtis:
            revoked = await self.revoke_family(chain_jti)
            total_revoked += revoked

        if total_revoked > 0:
            logger.warning(
                "BẢO MẬT: Đã thu hồi chuỗi - %d families, "
                "%d tokens (phát hiện tái sử dụng: %s)",
                len(chain_jtis),
                total_revoked,
                refresh_jti,
            )

        return len(chain_jtis)

    # ── BLACKLIST ─────────────────────────────────────────

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Kiểm tra token có trong blacklist không."""
        statement = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none() is not None

    async def add_to_blacklist(
        self,
        *,
        jti: str,
        token_type: str = "access",
        expires_at: datetime,
        user_id: Optional[uuid.UUID] = None,
    ) -> None:
        """Thêm token vào blacklist."""
        if expires_at.tzinfo is not None:
            expires_at = expires_at.astimezone(timezone.utc).replace(
                tzinfo=None
            )

        entry = TokenBlacklist(
            jti=jti,
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at,
        )
        self.db.add(entry)
        await self.db.flush()

    # ── CLEANUP ───────────────────────────────────────────

    async def cleanup_expired_verification_tokens(self) -> int:
        """Xóa verification tokens đã hết hạn hoặc đã sử dụng."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = delete(VerificationToken).where(
            (VerificationToken.expires_at < now)
            | (VerificationToken.is_used == True),  # noqa: E712
        )
        result = await self.db.execute(statement)
        await self.db.flush()
        deleted = result.rowcount
        logger.info("[Cleanup] Đã xóa %d verification tokens", deleted)
        return deleted

    async def cleanup_expired_blacklist(self) -> int:
        """Xóa token đã hết hạn khỏi blacklist."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = delete(TokenBlacklist).where(
            TokenBlacklist.expires_at < now,
        )
        result = await self.db.execute(statement)
        await self.db.flush()
        deleted = result.rowcount
        logger.info(
            "[Cleanup] Đã xóa %d token blacklist đã hết hạn", deleted
        )
        return deleted

    async def cleanup_expired_families(self) -> int:
        """Dọn dẹp token families đã hết hạn."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = delete(TokenFamily).where(
            TokenFamily.expires_at < now,
        )
        result = await self.db.execute(statement)
        await self.db.flush()
        deleted = result.rowcount
        logger.info("[Cleanup] Đã xóa %d token families", deleted)
        return deleted

    async def cleanup_all(self) -> dict[str, int]:
        """Dọn dẹp tất cả expired tokens."""
        blacklist_count = await self.cleanup_expired_blacklist()
        verification_count = (
            await self.cleanup_expired_verification_tokens()
        )
        families_count = await self.cleanup_expired_families()

        logger.info(
            "Cleanup hoàn tất: %d blacklist, %d verifications, %d families",
            blacklist_count,
            verification_count,
            families_count,
        )

        return {
            "blacklist_tokens": blacklist_count,
            "verification_tokens": verification_count,
            "token_families": families_count,
        }

    async def get_cleanup_stats(self) -> dict[str, int]:
        """Lấy thống kê các records cần cleanup."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        blacklist_stmt = (
            select(func.count())
            .select_from(TokenBlacklist)
            .where(TokenBlacklist.expires_at < now)
        )
        verification_stmt = (
            select(func.count())
            .select_from(VerificationToken)
            .where(
                (VerificationToken.expires_at < now)
                | (VerificationToken.is_used == True),  # noqa: E712
            )
        )

        bl_result = await self.db.execute(blacklist_stmt)
        vt_result = await self.db.execute(verification_stmt)

        return {
            "expired_blacklist_tokens": bl_result.scalar_one(),
            "expired_verification_tokens": vt_result.scalar_one(),
        }
