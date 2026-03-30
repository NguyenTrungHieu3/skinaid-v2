import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, case, desc, or_
from sqlmodel import select

from app.modules.audit.models.audit_log import AuditLog
from app.modules.users.models.user import User
from app.modules.auth.models.roles import Role
from app.modules.auth.models.user_roles import UserRole
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db):
        super().__init__(AuditLog, db)

    async def get_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        success: Optional[bool] = None,
        is_guest: Optional[bool] = None,
        search: Optional[str] = None,
        role_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lấy audit logs với filter và pagination.
        """
        stmt = select(
            AuditLog,
            User.user_name,
            User.email,
            func.string_agg(Role.role_name, ", ").label("role_names"),
        ).outerjoin(User, AuditLog.user_id == User.user_id).outerjoin(
            UserRole, User.user_id == UserRole.user_id
        ).outerjoin(
            Role, UserRole.role_id == Role.role_id
        ).group_by(AuditLog.audit_action_id, User.user_name, User.email)

        # Filters
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if success is not None:
            stmt = stmt.where(AuditLog.success == success)
        if is_guest is not None:
            stmt = stmt.where(AuditLog.is_guest == is_guest)

        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(or_(
                AuditLog.action.ilike(search_pattern),
                AuditLog.error_message.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.user_name.ilike(search_pattern)
            ))

        if role_name:
            subquery = select(UserRole.user_id).join(
                Role).where(Role.role_name == role_name)
            stmt = stmt.where(AuditLog.user_id.in_(subquery))

        count_stmt = select(func.count()).select_from(
            stmt.subquery()
        )
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar_one()

        stmt = stmt.order_by(desc(AuditLog.timestamp))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        logs = []
        for row in rows:
            audit_log, user_name, email, role_names = row
            log_dict = audit_log.to_dict()
            log_dict.update({
                "user_name": user_name,
                "email": email,
                "role_name": role_names,
            })
            logs.append(log_dict)

        return logs, total_count

    async def get_audit_stats(self) -> Dict[str, Any]:
        """Lấy thống kê audit logs."""
        res = await self.db.execute(
            select(
                func.count().label("total"),
                func.sum(case((AuditLog.success == True, 1), else_=0)
                         ).label("success")
            ).select_from(AuditLog)
        )
        total, success_count = res.one()
        total = total or 0
        success_count = success_count or 0
        success_rate = (success_count / total * 100) if total > 0 else 0

        res_actions = await self.db.execute(
            select(AuditLog.action, func.count().label("count"))
            .group_by(AuditLog.action)
            .order_by(desc("count"))
        )
        action_dist = {row.action: row.count for row in res_actions.all()}

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        yesterday = now - timedelta(hours=24)

        res_recent = await self.db.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.timestamp >= yesterday)
        )
        recent_count = res_recent.scalar_one()

        return {
            "total_logs": total,
            "success_rate": round(success_rate, 2),
            "action_distribution": action_dist,
            "recent_activity_24h": recent_count
        }
