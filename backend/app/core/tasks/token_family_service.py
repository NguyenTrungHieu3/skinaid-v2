from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text, select 
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
    """
    Create token family record
    
    Args:
        db: Database session
        user_id: User UUID string
        refresh_jti: Refresh token JTI
        access_jti: Access token JTI
        refresh_exp: Refresh token expiration
        parent_jti: Previous refresh token JTI (for rotation chain)
    """
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

    # Ensure timezone consistency for datetime objects by converting to naive UTC
    from datetime import timezone
    if refresh_exp.tzinfo is not None:
        # Convert to naive datetime in UTC
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
    logger.info(f"Created token family for user {user_id}, refresh_jti: {refresh_jti}")

async def check_token_family_revoked(
    db: AsyncSession, 
    refresh_jti: str
) -> bool: 
    """
    Check if token family is revoked
    
    Returns:
        True if revoked, False if not revoked or not found
    """
    query = text("""
        SELECT is_revoked FROM token_families
        WHERE refresh_token_jti = :jti
    """)

    result = await db.execute(query, {"jti": refresh_jti})
    row = result.first()

    return row[0] if row else False

async def revoke_token_family(
    db: AsyncSession, 
    jti: str
) -> int: 
    """
    Revoke token family by any JTI (refresh or access)
    Also adds tokens to blacklist
    
    Returns:
        Number of tokens revoked
    """
    # Find the family
    query = text("""
        SELECT refresh_token_jti, access_token_jti, expires_at
        FROM token_families
        WHERE refresh_token_jti = :jti
            OR access_token_jti = :jti
            AND is_revoked = false
    """)

    result = await db.execute(query, {"jti": jti})
    row = result.mappings().first()

    if not row: 
        logger.warning(f"Token family not found for jti: {jti}")
        return 0 
    
    refresh_jti = row["refresh_token_jti"]
    access_jti = row["access_token_jti"]
    expires_at = row["expires_at"]

    # List JTIs to Blacklist
    jtis_to_revoke = [refresh_jti]
    if access_jti: 
        jtis_to_revoke.append(access_jti)
    
    # add to blacklist
    for token_jti in jtis_to_revoke:
        # Determine token type based on comparison with refresh_jti
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

        # Ensure timezone consistency for datetime objects by converting to naive UTC
        from datetime import timezone
        if expires_at and expires_at.tzinfo is not None:
            # Convert to naive datetime in UTC
            expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
        
        revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await db.execute(insert_query, {
            "jti": token_jti,
            "revoked_at": revoked_at,
            "expires_at": expires_at,
            "token_type": token_type
        })

    # set is_revoked = true in family 
    update_query = text("""
        UPDATE token_families
        SET is_revoked = true
        WHERE refresh_token_jti = :jti
    """)

    await db.execute(update_query, {"jti": refresh_jti})
    await db.commit()

    logger.info(f"Revoked token family: {len(jtis_to_revoke)} tokens")
    
    return len(jtis_to_revoke)

async def revoke_entire_chain(db: AsyncSession, refresh_jti: str) -> int:
    """
    Revoke entire token chain (for reuse detection)
    Follows parent_jti links to revoke all related families
    
    Returns:
        Number of families revoked
    """
    # Find all families in the chain
    query = text("""
        WITH RECURSIVE token_chain AS (
            -- Start with the current token
            SELECT family_id, refresh_token_jti, parent_jti
            FROM token_families
            WHERE refresh_token_jti = :jti
            
            UNION ALL
            
            -- Follow parent links
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
    
    # Revoke all families in chain
    total_revoked = 0
    for chain_jti in chain_jtis:
        revoked = await revoke_token_family(db, chain_jti)
        total_revoked += revoked
    
    logger.warning(
        f"SECURITY: Revoked entire token chain ({len(chain_jtis)} families, "
        f"{total_revoked} tokens) due to reuse detection. Starting JTI: {refresh_jti}"
    )
    
    return len(chain_jtis)


async def cleanup_expired_token_families(db: AsyncSession) -> int:
    """Cleanup expired token families"""
    query = text("""
        DELETE FROM token_families
        WHERE expires_at < NOW()
    """)
    
    result = await db.execute(query)
    await db.commit()
    
    deleted_count = result.rowcount
    logger.info(f"Cleaned up {deleted_count} expired token families")
    
    return deleted_count
