"""
Admin Audit Log Service

This service provides functionality to record admin actions
for compliance, security, and debugging purposes.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json

from app.modules.admin.models.audit_log import AdminAuditLog, AuditLogCreate, AuditLogResponse

logger = logging.getLogger(__name__)


class AdminAuditService:
    """Service để quản lý admin audit logs"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
        metadata: Optional[Dict[str, Any]] = None,
        http_method: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> Optional[AdminAuditLog]:
        """
        Ghi lại hành động của admin vào audit trail.
        
        Args:
            admin_user_id: UUID của admin thực hiện hành động
            admin_email: Email của admin
            admin_role: Vai trò của admin (admin, moderator, etc.)
            action: Hành động được thực hiện (CREATE_USER, UPDATE_GUIDE, etc.)
            resource_type: Loại tài nguyên (user, first_aid_guide, etc.)
            resource_id: ID của tài nguyên bị ảnh hưởng
            description: Mô tả dễ đọc
            changes: Dict chứa trạng thái trước/sau
            metadata: Context bổ sung (request_id, etc.)
            http_method: Phương thức HTTP (POST, PUT, DELETE, etc.)
            endpoint: API endpoint
            ip_address: IP của client
            user_agent: User agent của client
            status: success, failed, hoặc partial
            error_message: Thông báo lỗi nếu thất bại
            duration_ms: Thời gian thực hiện tính bằng mili giây
        
        Returns:
            Bản ghi audit log đã tạo, hoặc None nếu ghi log thất bại
        """
        try:
            # Serialize JSONB fields to JSON strings for AsyncPG
            changes_json = json.dumps(changes) if changes else None
            metadata_json = json.dumps(metadata) if metadata else None
            
            log_entry = AdminAuditLog(
                admin_user_id=admin_user_id,
                admin_email=admin_email,
                admin_role=admin_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                changes=changes_json,  # type: ignore
                metadata=metadata_json,  # type: ignore
                http_method=http_method,
                endpoint=endpoint,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            await self.db.refresh(log_entry)
            
            logger.info(
                f"Audit log đã được tạo: action={action}, admin={admin_email}, "
                f"resource={resource_type}:{resource_id}, status={status}"
            )
            
            return log_entry
            
        except Exception as e:
            logger.error(f"Thất bại khi tạo audit log: {e}", exc_info=True)
            # Don't raise - we don't want audit logging failures to break the main operation
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
        """
        Lấy audit logs với các bộ lọc tùy chọn.
        
        Args:
            admin_user_id: Lọc theo admin user
            action: Lọc theo loại hành động
            resource_type: Lọc theo loại tài nguyên
            resource_id: Lọc theo ID tài nguyên
            status: Lọc theo trạng thái
            limit: Số lượng kết quả tối đa
            offset: Số lượng kết quả bỏ qua
        
        Returns:
            Danh sách các bản ghi audit log
        """
        try:
            query = select(AdminAuditLog)
            
            # Apply filters
            if admin_user_id:
                query = query.where(AdminAuditLog.admin_user_id == admin_user_id)
            if action:
                query = query.where(AdminAuditLog.action == action)
            if resource_type:
                query = query.where(AdminAuditLog.resource_type == resource_type)
            if resource_id:
                query = query.where(AdminAuditLog.resource_id == resource_id)
            if status:
                query = query.where(AdminAuditLog.status == status)
            
            # Order by most recent first
            query = query.order_by(AdminAuditLog.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            return list(logs)
            
        except Exception as e:
            logger.error(f"Thất bại khi lấy audit logs: {e}", exc_info=True)
            return []
    
    async def get_log_by_id(self, log_id: UUID) -> Optional[AdminAuditLog]:
        """Lấy một audit log cụ thể theo ID"""
        try:
            result = await self.db.execute(
                select(AdminAuditLog).where(AdminAuditLog.log_id == log_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Thất bại khi lấy audit log: {e}", exc_info=True)
            return None
    
    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> List[AdminAuditLog]:
        """
        Lấy toàn bộ lịch sử audit cho một tài nguyên cụ thể.
        
        Args:
            resource_type: Loại tài nguyên (user, first_aid_guide, etc.)
            resource_id: ID của tài nguyên
            limit: Số lượng mục tối đa trả về
        
        Returns:
            Danh sách các bản ghi audit log cho tài nguyên
        """
        return await self.get_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
