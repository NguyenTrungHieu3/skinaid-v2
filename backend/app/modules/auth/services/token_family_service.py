from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text
from datetime import datetime, timezone
import uuid
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

async def create_token_family(
    db: AsyncSession,
    user_id: str,
    refresh_jti: str,
    access_jti: str,
    refresh_exp: datetime,
    parent_jti: Optional[str] = None
) -> None:
    return await TokenFamilyService.create_token_family(
        db=db,
        user_id=user_id,
        refresh_jti=refresh_jti,
        access_jti=access_jti,
        refresh_exp=refresh_exp,
        parent_jti=parent_jti
    )


async def check_token_family_revoked(
    db: AsyncSession,
    refresh_jti: str
) -> bool:
    return await TokenFamilyService.check_token_family_revoked(
        db=db,
        refresh_jti=refresh_jti
    )


async def revoke_token_family(
    db: AsyncSession,
    jti: str
) -> int:
    return await TokenFamilyService.revoke_token_family(
        db=db,
        jti=jti
    )


async def revoke_entire_chain(db: AsyncSession, refresh_jti: str) -> int:
    return await TokenFamilyService.revoke_entire_chain(
        db=db,
        refresh_jti=refresh_jti
    )


class TokenFamilyService:
    
    @staticmethod
    async def create_token_family(
        db: AsyncSession,
        user_id: str,
        refresh_jti: str,
        access_jti: str,
        refresh_exp: datetime,
        parent_jti: Optional[str] = None
    ) -> None:
        """Tạo bản ghi token family"""
        family_id = uuid.uuid4()
        
        query = text("""
            INSERT INTO token_families (
                family_id, user_id, refresh_token_jti, access_token_jti,
                parent_jti, expires_at, created_at, is_revoked
            )
            VALUES (
                CAST(:family_id AS UUID),
                CAST(:user_id AS UUID),
                :refresh_jti,
                :access_jti,
                :parent_jti,
                :expires_at,
                :created_at,
                false
            )
        """)
        
        # Chuẩn hóa múi giờ
        if refresh_exp.tzinfo is not None:
            refresh_exp = refresh_exp.astimezone(timezone.utc).replace(tzinfo=None)
        
        created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await db.execute(query, {
            "family_id": family_id,
            "user_id": user_id,
            "refresh_jti": refresh_jti,
            "access_jti": access_jti,
            "parent_jti": parent_jti,
            "expires_at": refresh_exp,
            "created_at": created_at
        })
        
        await db.commit()
        logger.info(f"Tạo token family: user={user_id}, jti={refresh_jti}")
    
    @staticmethod
    async def check_token_family_revoked(
        db: AsyncSession,
        refresh_jti: str
    ) -> bool:
        """Kiểm tra token family có bị revoked không"""
        query = text("""
            SELECT is_revoked FROM token_families
            WHERE refresh_token_jti = :jti
        """)
        
        result = await db.execute(query, {"jti": refresh_jti})
        row = result.first()
        
        return row[0] if row else False
    
    @staticmethod
    async def revoke_token_family(
        db: AsyncSession,
        jti: str
    ) -> int:
        """Thu hồi token family và thêm vào blacklist"""
        query = text("""
            SELECT refresh_token_jti, access_token_jti, expires_at
            FROM token_families
            WHERE (refresh_token_jti = :jti OR access_token_jti = :jti)
                AND is_revoked = false
        """)
        
        result = await db.execute(query, {"jti": jti})
        row = result.mappings().first()
        
        if not row:
            logger.warning(f"Không tìm thấy token family: jti={jti}")
            return 0
        
        refresh_jti = row["refresh_token_jti"]
        access_jti = row["access_token_jti"]
        expires_at = row["expires_at"]
        
        # Thu hồi các token
        jtis_to_revoke = [refresh_jti]
        if access_jti:
            jtis_to_revoke.append(access_jti)
        
        for token_jti in jtis_to_revoke:
            token_type = 'refresh' if token_jti == refresh_jti else 'access'
            
            insert_query = text("""
                INSERT INTO token_blacklist(
                    tokenblacklist_id, jti, revoked_at, expires_at, token_type
                )
                VALUES(
                    gen_random_uuid(),
                    :jti,
                    :revoked_at,
                    :expires_at,
                    :token_type
                )
                ON CONFLICT(jti) DO NOTHING
            """)
            
            if expires_at and expires_at.tzinfo is not None:
                expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            
            revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            await db.execute(insert_query, {
                "jti": token_jti,
                "revoked_at": revoked_at,
                "expires_at": expires_at,
                "token_type": token_type
            })
        
        # Cập nhật họ token
        update_query = text("""
            UPDATE token_families
            SET is_revoked = true
            WHERE refresh_token_jti = :jti
        """)
        
        await db.execute(update_query, {"jti": refresh_jti})
        await db.commit()
        
        logger.info(f"Revoked token family: {len(jtis_to_revoke)} tokens")
        return len(jtis_to_revoke)
    
    @staticmethod
    async def revoke_entire_chain(db: AsyncSession, refresh_jti: str) -> int:
        """Thu hồi toàn bộ token chain (phát hiện reuse)"""
        query = text("""
            WITH RECURSIVE token_chain AS (
                SELECT family_id, refresh_token_jti, parent_jti
                FROM token_families
                WHERE refresh_token_jti = :jti
                
                UNION ALL
                
                SELECT tf.family_id, tf.refresh_token_jti, tf.parent_jti
                FROM token_families tf
                INNER JOIN token_chain tc ON tf.refresh_token_jti = tc.parent_jti
            )
            SELECT refresh_token_jti FROM token_chain
        """)
        
        result = await db.execute(query, {"jti": refresh_jti})
        chain_jtis = [row[0] for row in result.fetchall()]
        
        if not chain_jtis:
            return 0
        
        total_revoked = 0
        service = TokenFamilyService()
        
        for chain_jti in chain_jtis:
            revoked = await service.revoke_token_family(db, chain_jti)
            total_revoked += revoked
        
        logger.warning(
            f"BẢO MẬT: Revoked chain - {len(chain_jtis)} families, "
            f"{total_revoked} tokens (reuse detected: {refresh_jti})"
        )
        
        return len(chain_jtis)