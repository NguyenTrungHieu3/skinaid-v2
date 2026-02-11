from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, Dict, Any, List
import logging

from app.modules.admin.models.audit_log import AdminAuditLog
from app.modules.admin.repository.admin_audit_repository import AdminAuditRepository

logger = logging.getLogger(__name__)


class AdminAuditService:
    def __init__(self, db: AsyncSession):
        self.repository = AdminAuditRepository(db)

    async def log_action(
        self,
        admin_user_id: UUID,
        admin_email: str,
        admin_role: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        http_method: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> Optional[AdminAuditLog]:
        try:
            log_entry = AdminAuditLog(
                admin_user_id=admin_user_id,
                admin_email=admin_email,
                admin_role=admin_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                changes=changes,
                meta_data=meta_data,
                http_method=http_method,
                endpoint=endpoint,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
            )

            # Use repository to create
            return await self.repository.create(log_entry)

        except Exception as e:
            logger.error(f"Thất bại khi tạo audit log: {e}", exc_info=True)
            return None

    async def get_logs(
        self,
        admin_user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AdminAuditLog]:
        try:
            logs = await self.repository.get_logs(
                admin_user_id=admin_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status=status,
                limit=limit,
                offset=offset
            )
            return list(logs)
        except Exception as e:
            logger.error(f"Thất bại khi lấy audit logs: {e}", exc_info=True)
            return []

    async def get_log_by_id(self, log_id: UUID) -> Optional[AdminAuditLog]:
        try:
            return await self.repository.get_by_id(log_id)
        except Exception as e:
            logger.error(f"Thất bại khi lấy audit log: {e}", exc_info=True)
            return None

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> List[AdminAuditLog]:
        return await self.get_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
