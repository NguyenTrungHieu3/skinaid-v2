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
        Chuyển đổi hàng database thành instance AuditLog.
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
                    :guest_session_id, CAST(:details AS jsonb), :timestamp
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
                f"Đã tạo audit log: hành động={action}, "
                f"người dùng={user_identifier}, "
                f"thành công={success}"
            )

            return audit_log

        except Exception as e:
            logger.error(
                f"Không thể ghi audit event: hành động={action}, "
                f"user_id={user_id}, lỗi={str(e)}"
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
        search: Optional[str] = None,
        role_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Truy vấn audit logs với bộ lọc.

        Trả về:
            Tuple[List[Dict[str, Any]], int]: (logs, total_count)
        """
        try:
            # Xây dựng bộ lọc
            filter_fields = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "success": success,
                "is_guest": is_guest
            }

            where_clauses = []
            for field, value in filter_fields.items():
                if value is not None:
                    where_clauses.append(f"al.{field} = :{field}")

            params = {
                field: value
                for field, value in filter_fields.items()
                if value is not None
            }

            if start_date is not None:
                where_clauses.append("al.timestamp >= :start_date")
                params["start_date"] = start_date

            if end_date is not None:
                where_clauses.append("al.timestamp <= :end_date")
                params["end_date"] = end_date

            # Add search filter
            if search is not None and search.strip():
                search_pattern = f"%{search.strip()}%"
                where_clauses.append(
                    "(al.action ILIKE :search OR "
                    "u.user_name ILIKE :search OR "
                    "u.email ILIKE :search OR "
                    "al.error_message ILIKE :search)"
                )
                params["search"] = search_pattern

            # Add role_name filter
            if role_name is not None and role_name.strip():
                where_clauses.append(
                    "EXISTS ("
                    "SELECT 1 FROM user_roles ur "
                    "JOIN roles r ON ur.role_id = r.role_id "
                    "WHERE ur.user_id = al.user_id AND r.role_name = :role_name"
                    ")"
                )
                params["role_name"] = role_name.strip()

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # TRUY VẤN 1: Đếm tổng số bản ghi phù hợp
            count_query = text(f"""
                SELECT COUNT(*)
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE {where_sql}
            """)

            # Ensure we are using the session correctly
            count_result = await self.db.execute(count_query, params)
            total_count = count_result.scalar() or 0

            # TRUY VẤN 2: Lấy logs phân trang
            params["limit"] = limit
            params["offset"] = offset

            query_sql = text(f"""
                SELECT
                    al.audit_action_id, al.user_id, al.action, al.resource_type, al.resource_id,
                    al.ip_address, al.user_agent, al.success, al.error_message, al.is_guest,
                    al.guest_session_id, al.details, al.timestamp,
                    u.user_name, u.email,
                    (
                        SELECT STRING_AGG(r.role_name, ', ')
                        FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.role_id
                        WHERE ur.user_id = al.user_id
                    ) as role_name
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE {where_sql}
                ORDER BY al.timestamp DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(query_sql, params)
            rows = result.fetchall()

            logs = []
            for row in rows:
                log_dict = {
                    "audit_action_id": row.audit_action_id,
                    "user_id": row.user_id,
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "success": row.success,
                    "error_message": row.error_message,
                    "is_guest": row.is_guest,
                    "guest_session_id": row.guest_session_id,
                    "details": row.details,
                    "timestamp": row.timestamp,
                    "user_name": row.user_name,
                    "email": row.email,
                    "role_name": row.role_name
                }
                logs.append(log_dict)

            logger.info(
                f"Đã lấy {len(logs)}/{total_count} audit logs với bộ lọc: "
                f"{', '.join(f'{k}={v}' for k, v in filter_fields.items() if v is not None)}"
            )
            return logs, total_count

        except Exception as e:
            logger.error(f"Không thể lấy audit logs: {str(e)}")
            raise

    async def get_audit_stats(self) -> Dict[str, Any]:
        """Lấy thống kê audit cơ bản."""
        try:
            # Truy vấn 1: Tổng logs và số lượng thành công
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

            # Truy vấn 2: Phân bố hành động
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

            # Truy vấn 3: Hoạt động gần đây (24h qua)
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

            logger.info("Đã lấy thống kê audit")
            return stats

        except Exception as e:
            logger.error(f"Không thể lấy thống kê audit: {str(e)}")
            raise

    # Phương thức tiện ích cho các sự kiện phổ biến

    async def log_login(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Ghi lại lần thử đăng nhập của người dùng."""
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
        """Ghi lại việc đăng xuất của người dùng."""
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
        guest_session_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Ghi lại sự kiện upload file."""
        action = "guest_upload" if is_guest else "user_file_upload"

        upload_details = {}
        if file_name:
            upload_details["file_name"] = file_name
        if file_size is not None:
            upload_details["file_size"] = file_size
        if file_path:
            upload_details["file_path"] = file_path
        
        # Gộp với chi tiết bổ sung nếu được cung cấp
        if details:
            upload_details.update(details)

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
            details=upload_details if upload_details else None
        )
    

    async def log_wound_analysis_started(
        self, 
        correlation_id: str, 
        user_id: Optional[UUID] = None, 
        file_path: Optional[str] = None,
        source: Optional[str] = None,
        is_guest: bool = False,
        guest_session_id: Optional[UUID] = None
    )-> AuditLog:
        return await self.log_event(
            action="wound_analysis_started", 
            user_id=user_id, 
            resource_type="wound_analysis", 
            resource_id=correlation_id, 
            is_guest=is_guest, 
            guest_session_id=guest_session_id, 
            details={
                "file_path": file_path, 
                "source": source, 
                "correlation_id": correlation_id
            }
        )
    
    async def log_wound_analysis_completed(
        self, 
        correlation_id: str, 
        user_id: Optional[UUID] = None, 
        analysis_id: Optional[str] = None,
        file_path: Optional[str] = None,
        ai_model_version: Optional[str] = None,
        total_detections: Optional[int] = None,
        average_confidence: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        is_guest: bool = False,
        guest_session_id: Optional[UUID] = None
    )-> AuditLog: 
        return await self.log_event(
            action="wound_analysis_completed", 
            user_id=user_id, 
            resource_type="wound_analysis",
            resource_id=analysis_id or correlation_id,
            is_guest=is_guest,
            guest_session_id=guest_session_id,
            details={
                "file_path": file_path,
                "ai_model_version": ai_model_version,
                "total_detections": total_detections,
                "average_confidence": average_confidence,
                "processing_time_ms": processing_time_ms,
                "correlation_id": correlation_id
            }
        )
    
    async def log_wound_analysis_failed(
        self,
        correlation_id: str,
        user_id: Optional[UUID] = None,
        file_path: Optional[str] = None,
        reason: Optional[str] = None,
        error_code: Optional[str] = None,
        is_guest: bool = False,
        guest_session_id: Optional[UUID] = None
    ) -> AuditLog:
        return await self.log_event(
            action="wound_analysis_failed",
            user_id=user_id,
            resource_type="wound_analysis",
            resource_id=correlation_id,
            success=False,
            error_message=reason,
            is_guest=is_guest,
            guest_session_id=guest_session_id,
            details={
                "file_path": file_path,
                "reason": reason,
                "error_code": error_code,
                "correlation_id": correlation_id
            }
        )
    
    