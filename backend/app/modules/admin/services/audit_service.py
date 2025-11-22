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
    """Service for managing admin audit logs"""
    
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
        Log an admin action to the audit trail.
        
        Args:
            admin_user_id: UUID of the admin performing the action
            admin_email: Email of the admin
            admin_role: Role of the admin (admin, moderator, etc.)
            action: Action being performed (CREATE_USER, UPDATE_GUIDE, etc.)
            resource_type: Type of resource (user, first_aid_guide, etc.)
            resource_id: ID of the affected resource  
            description: Human-readable description
            changes: Dict containing before/after state
            metadata: Additional context (request_id, etc.)
            http_method: HTTP method (POST, PUT, DELETE, etc.)
            endpoint: API endpoint
            ip_address: Client IP
            user_agent: Client user agent
            status: success, failed, or partial
            error_message: Error message if failed
            duration_ms: Operation duration in milliseconds
        
        Returns:
            Created audit log entry, or None if logging failed
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
                f"Audit log created: action={action}, admin={admin_email}, "
                f"resource={resource_type}:{resource_id}, status={status}"
            )
            
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
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
        Retrieve audit logs with optional filters.
        
        Args:
            admin_user_id: Filter by admin user
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of audit log entries
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
            logger.error(f"Failed to retrieve audit logs: {e}", exc_info=True)
            return []
    
    async def get_log_by_id(self, log_id: UUID) -> Optional[AdminAuditLog]:
        """Get a specific audit log by ID"""
        try:
            result = await self.db.execute(
                select(AdminAuditLog).where(AdminAuditLog.log_id == log_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}", exc_info=True)
            return None
    
    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> List[AdminAuditLog]:
        """
        Get the complete audit history for a specific resource.
        
        Args:
            resource_type: Type of resource (user, first_aid_guide, etc.)
            resource_id: ID of the resource
            limit: Maximum number of entries to return
        
        Returns:
            List of audit log entries for the resource
        """
        return await self.get_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
