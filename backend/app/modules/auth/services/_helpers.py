import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.modules.auth.models.roles import Role
from app.modules.auth.models.user_roles import UserRole

logger = logging.getLogger(__name__)

use_mock_email = (
    os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"
)
if use_mock_email:
    from app.utils.mock_email_service import mock_email_service as email_service
    logger.info("Sử dụng dịch vụ email MOCK")
else:
    from app.utils.email_service import email_service
    logger.info("Sử dụng dịch vụ email THỰC")

def get_current_utc_time() -> datetime:
    """
    Lấy thời gian UTC hiện tại mà không có thông tin múi giờ.
    
    Returns:
        datetime: Thời gian UTC hiện tại không có thông tin múi giờ
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

async def execute_query_one(
    db: AsyncSession,
    sql: text,
    params: dict
) -> Optional[dict]:
    result = await db.execute(sql, params)
    row = result.mappings().first()
    return dict(row) if row else None


async def execute_query_all(
    db: AsyncSession,
    sql: text,
    params: dict
) -> list[dict]:
    result = await db.execute(sql, params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def commit_with_rollback(db: AsyncSession):
    try:
        await db.commit()
    except Exception as e:
        logger.error("Lỗi khi commit transaction: %s", str(e))
        try:
            await db.rollback()
            logger.info("Giao dịch đã được rollback do lỗi")
        except Exception as rollback_error:
            logger.error(
                "Không thể rollback giao dịch: %s",
                str(rollback_error),
            )
        raise

def raise_if_validation_fails(
    validation_result: Optional[str],
    error_code: str
):
    if validation_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result,
        )

async def send_email_async(
    email_task,
    email_type: str,
    recipient: str
):
    try:
        asyncio.create_task(email_task)
        logger.info(
            "Email %s đã được đưa vào hàng đợi cho: %s",
            email_type,
            recipient,
        )
    except Exception as e:
        logger.error(
            "Không thể đưa email %s vào hàng đợi cho %s: %s",
            email_type,
            recipient,
            str(e),
        )

async def load_user_roles(
    db: AsyncSession,
    user_id: uuid.UUID
) -> list[UserRole]:
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

    roles_rows = await execute_query_all(db, roles_sql, {"user_id": user_id})

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

    return user_roles


def get_email_service():
    return email_service
