from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.base_repository import BaseRepository
from app.modules.admin.models.audit_log import AdminAuditLog


class AdminAuditRepository(BaseRepository[AdminAuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(AdminAuditLog, db)

    async def get_logs(
        self,
        admin_user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AdminAuditLog]:
        """
        Lấy danh sách audit logs với các bộ lọc.
        """
        query = select(self.model)

        if admin_user_id:
            query = query.where(self.model.admin_user_id == admin_user_id)
        if action:
            query = query.where(self.model.action == action)
        if resource_type:
            query = query.where(self.model.resource_type == resource_type)
        if resource_id:
            query = query.where(self.model.resource_id == resource_id)
        if status:
            query = query.where(self.model.status == status)

        # Order by most recent first
        query = query.order_by(desc(self.model.created_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()
