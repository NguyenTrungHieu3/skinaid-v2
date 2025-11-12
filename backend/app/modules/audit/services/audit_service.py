from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
import logging
import json

from app.modules.audit.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _map_row_to_audit_log(row) -> AuditLog:
        """
        Convert database row to AuditLog instance.
        """
        return AuditLog(
            audit_action_id=row.audit_action_id,
            user_id=row.user_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            ip_address=row.ip_address,
            user_agent=row.user_agent,
            success=row.success,
            error_message=row.error_message,
            is_guest=row.is_guest,
            guest_session_id=row.guest_session_id,
            details=row.details,
            timestamp=row.timestamp
        )

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

            audit_action_id = uuid4()
            timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

            details_json = json.dumps(details) if details else None

            query = text("""
                INSERT INTO audit_logs(
                    audit_action_id, user_id, action, resource_type, resource_id,
                    ip_address, user_agent, success, error_message, is_guest,
                    guest_session_id, details, timestamp
                ) VALUES (
                    :audit_action_id, :user_id, :action, :resource_type, :resource_id,
                    :ip_address, :user_agent, :success, :error_message, :is_guest,
                    :guest_session_id, :details::jsonb, :timestamp
                )
                RETURNING
                    audit_action_id, user_id, action, resource_type, resource_id,
                    ip_address, user_agent, success, error_message, is_guest,
                    guest_session_id, details, timestamp
            """)

            result = await self.db.execute(
                query,
                {
                    "audit_action_id": audit_action_id,
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "success": success,
                    "error_message": error_message,
                    "is_guest": is_guest,
                    "guest_session_id": guest_session_id,
                    "details": details_json,
                    "timestamp": timestamp
                }
            )

            await self.db.commit()

            row = result.fetchone()

            audit_log = self._map_row_to_audit_log(row)

            user_identifier = str(user_id) if user_id else (
                f"guest:{guest_session_id}" if guest_session_id else "unknown"
            )
            logger.info(
                f"Audit log created: action={action}, "
                f"user={user_identifier}, "
                f"success={success}"
            )

            return audit_log

        except Exception as e:
            logger.error(
                f"Failed to log audit event: action={action}, "
                f"user_id={user_id}, error={str(e)}"
            )
            await self.db.rollback()
            raise

    async def get_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        success: Optional[bool] = None,
        is_guest: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[AuditLog], int]: 
        """
        Query audit logs with filtering.
        
        Returns:
            Tuple[List[AuditLog], int]: (logs, total_count)
        """
        try:
            # Build filters
            filter_fields = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "success": success,
                "is_guest": is_guest
            }

            where_clauses = [
                f"{field} = :{field}"
                for field, value in filter_fields.items()
                if value is not None
            ]

            params = {
                field: value
                for field, value in filter_fields.items()
                if value is not None
            }

            if start_date is not None:
                where_clauses.append("timestamp >= :start_date")
                params["start_date"] = start_date

            if end_date is not None:
                where_clauses.append("timestamp <= :end_date")
                params["end_date"] = end_date

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # QUERY 1: Count total matching records
            count_query = text(f"""
                SELECT COUNT(*)
                FROM audit_logs
                WHERE {where_sql}
            """)

            count_result = await self.db.execute(count_query, params)
            total_count = count_result.scalar() or 0

            # QUERY 2: Get paginated logs
            params["limit"] = limit
            params["offset"] = offset

            query_sql = text(f"""
                SELECT
                    audit_action_id, user_id, action, resource_type, resource_id,
                    ip_address, user_agent, success, error_message, is_guest,
                    guest_session_id, details, timestamp
                FROM audit_logs
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(query_sql, params)
            rows = result.fetchall()

            logs = [self._map_row_to_audit_log(row) for row in rows]

            logger.info(
                f"Retrieved {len(logs)}/{total_count} audit logs with filters: "
                f"{', '.join(f'{k}={v}' for k, v in filter_fields.items() if v is not None)}"
            )
            return logs, total_count

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {str(e)}")
            raise

    async def get_audit_stats(self) -> Dict[str, Any]:
        """Get basic audit statistics."""
        try:
            # Query 1: Total logs and success count
            count_query = text("""
                SELECT
                    COUNT(*) AS total_logs,
                    COUNT(*) FILTER (WHERE success = true) AS success_count
                FROM audit_logs
            """)

            count_result = await self.db.execute(count_query)
            count_row = count_result.fetchone()

            total_logs = count_row.total_logs or 0
            success_count = count_row.success_count or 0
            success_rate = (success_count / total_logs * 100) if total_logs > 0 else 0

            # Query 2: Action distribution
            action_query = text("""
                SELECT
                    action,
                    COUNT(*) as count
                FROM audit_logs
                GROUP BY action
                ORDER BY count DESC
            """)

            action_result = await self.db.execute(action_query)
            action_rows = action_result.fetchall()

            action_distribution = {row.action: row.count for row in action_rows}

            # Query 3: Recent activity (last 24h)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            yesterday = now - timedelta(hours=24)

            recent_query = text("""
                SELECT COUNT(*) as recent_count
                FROM audit_logs
                WHERE timestamp >= :yesterday
            """)

            recent_result = await self.db.execute(recent_query, {"yesterday": yesterday})
            recent_row = recent_result.fetchone()
            recent_activity = recent_row.recent_count or 0

            stats = {
                "total_logs": total_logs,
                "success_rate": round(success_rate, 2),
                "action_distribution": action_distribution,
                "recent_activity_24h": recent_activity
            }

            logger.info("Retrieved audit statistics")
            return stats

        except Exception as e:
            logger.error(f"Failed to retrieve audit statistics: {str(e)}")
            raise

    # Convenience methods for common events

    async def log_login(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log user login attempt."""
        return await self.log_event(
            action="login",
            user_id=user_id,
            success=success,
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message
        )

    async def log_logout(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log user logout."""
        return await self.log_event(
            action="logout",
            user_id=user_id,
            success=True,
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def log_file_upload(
        self,
        user_id: Optional[UUID] = None,
        file_path: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        is_guest: bool = False,
        guest_session_id: Optional[UUID] = None
    ) -> AuditLog:
        """Log file upload event."""
        action = "guest_upload" if is_guest else "user_file_upload"

        details = {}
        if file_name:
            details["file_name"] = file_name
        if file_size is not None:
            details["file_size"] = file_size
        if file_path:
            details["file_path"] = file_path

        return await self.log_event(
            action=action,
            user_id=user_id,
            success=success,
            resource_type="file",
            resource_id=file_path,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            is_guest=is_guest,
            guest_session_id=guest_session_id,
            details=details if details else None
        )