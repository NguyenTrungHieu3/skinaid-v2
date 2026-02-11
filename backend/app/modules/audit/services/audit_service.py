import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from app.modules.audit.models.audit_log import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas.api import AuditLogFilterParams

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def log_event(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        success: bool = True,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        is_guest: bool = False,
        guest_session_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        try:
            if error_message and len(error_message) > 500:
                error_message = error_message[:497] + "..."
            if user_agent and len(user_agent) > 500:
                user_agent = user_agent[:497] + "..."

            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
                is_guest=is_guest,
                guest_session_id=guest_session_id,
                details=details
            )

            return await self.repository.create(audit_log)

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            raise e

    async def get_audit_logs(
        self,
        filters: AuditLogFilterParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        offset = (filters.page - 1) * filters.limit
        return await self.repository.get_audit_logs(
            user_id=filters.user_id,
            action=filters.action,
            resource_type=filters.resource_type,
            success=filters.success,
            is_guest=filters.is_guest,
            search=filters.search,
            role_name=filters.role_name,
            start_date=filters.start_date,
            end_date=filters.end_date,
            limit=filters.limit,
            offset=offset
        )

    async def get_audit_stats(self) -> Dict[str, Any]:
        return await self.repository.get_audit_stats()
