from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.modules.auth.models.token_family import TokenFamily
from app.modules.auth.models.verification_token import VerificationToken


class TokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_verification_token(
        self,
        token: VerificationToken,
    ) -> VerificationToken:
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
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = select(VerificationToken).where(
            VerificationToken.email == email,
            VerificationToken.token == token,
            VerificationToken.token_type == token_type,
            VerificationToken.is_used == False,
            VerificationToken.expires_at > now,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def mark_token_used(self, token_id: UUID) -> None:
        statement = select(VerificationToken).where(
            VerificationToken.token_id == token_id,
        )
        result = await self.db.execute(statement)
        token_entity = result.scalar_one_or_none()
        if token_entity:
            token_entity.is_used = True
            token_entity.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.db.flush()

    async def invalidate_previous_tokens(self, email: str, token_type: str) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = select(VerificationToken).where(
            VerificationToken.email == email,
            VerificationToken.token_type == token_type,
            VerificationToken.is_used == False,
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
        return count

    async def delete_tokens_by_email(
        self,
        email: str,
        token_type: Optional[str] = None,
    ) -> int:
        stmt = delete(VerificationToken).where(VerificationToken.email == email)
        if token_type:
            stmt = stmt.where(VerificationToken.token_type == token_type)
        result = await self.db.execute(stmt)
        return result.rowcount

    # Token families

    async def create_token_family(
        self,
        *,
        user_id: UUID,
        refresh_jti: str,
        access_jti: Optional[str] = None,
        expires_at: datetime,
        parent_jti: Optional[str] = None,
    ) -> TokenFamily:
        if expires_at.tzinfo is not None:
            expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)

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
        statement = select(TokenFamily.is_revoked).where(
            TokenFamily.refresh_token_jti == refresh_jti,
        )
        result = await self.db.execute(statement)
        row = result.scalar_one_or_none()
        return bool(row) if row is not None else False

    async def get_family_by_jti(self, jti: str) -> Optional[TokenFamily]:
        statement = select(TokenFamily).where(
            (TokenFamily.refresh_token_jti == jti)
            | (TokenFamily.access_token_jti == jti),
            TokenFamily.is_revoked == False,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_family(self, jti: str) -> int:
        family = await self.get_family_by_jti(jti)
        if not family:
            return 0

        now = datetime.now(timezone.utc)
        redis = get_redis()

        jtis_to_revoke: list[tuple[str, int]] = [
            (family.refresh_token_jti, self._calc_ttl(family.expires_at, now)),
        ]
        if family.access_token_jti:
            jtis_to_revoke.append(
                (family.access_token_jti, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
            )

        async with redis.pipeline(transaction=False) as pipe:
            for token_jti, ttl in jtis_to_revoke:
                pipe.set(f"blacklist:{token_jti}", 1, ex=ttl)
            await pipe.execute()

        family.is_revoked = True
        await self.db.flush()

        return len(jtis_to_revoke)

    async def revoke_entire_chain(self, refresh_jti: str) -> int:
        chain_jtis: list[str] = []
        current_jti = refresh_jti

        while current_jti:
            chain_jtis.append(current_jti)
            statement = select(TokenFamily.parent_jti).where(
                TokenFamily.refresh_token_jti == current_jti,
            )
            result = await self.db.execute(statement)
            current_jti = result.scalar_one_or_none()

        children_to_check = [refresh_jti]
        while children_to_check:
            parent_jti = children_to_check.pop(0)
            statement = select(TokenFamily.refresh_token_jti).where(
                TokenFamily.parent_jti == parent_jti,
            )
            result = await self.db.execute(statement)
            for child_jti in result.scalars().all():
                if child_jti not in chain_jtis:
                    chain_jtis.append(child_jti)
                    children_to_check.append(child_jti)

        total_revoked = 0
        for chain_jti in chain_jtis:
            total_revoked += await self.revoke_family(chain_jti)

        return total_revoked

    # Cleanup

    async def cleanup_expired_verification_tokens(self) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = delete(VerificationToken).where(
            (VerificationToken.expires_at < now)
            | (VerificationToken.is_used == true()),
        )
        result = await self.db.execute(statement)
        await self.db.flush()
        return result.rowcount

    async def cleanup_expired_families(self) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = delete(TokenFamily).where(TokenFamily.expires_at < now)
        result = await self.db.execute(statement)
        await self.db.flush()
        return result.rowcount

    async def cleanup_all(self) -> dict[str, int]:
        return {
            "verification_tokens": await self.cleanup_expired_verification_tokens(),
            "token_families": await self.cleanup_expired_families(),
        }

    async def get_cleanup_stats(self) -> dict[str, int]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        vt_result = await self.db.execute(
            select(func.count())
            .select_from(VerificationToken)
            .where(
                (VerificationToken.expires_at < now)
                | (VerificationToken.is_used == true()),
            )
        )
        fam_result = await self.db.execute(
            select(func.count())
            .select_from(TokenFamily)
            .where(TokenFamily.expires_at < now)
        )

        return {
            "expired_verification_tokens": vt_result.scalar_one(),
            "expired_token_families": fam_result.scalar_one(),
        }

    @staticmethod
    def _calc_ttl(expires_at: Optional[datetime], now: datetime) -> int:
        if expires_at is None:
            return 7 * 24 * 3600
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return max(int((expires_at - now).total_seconds()), 1)
