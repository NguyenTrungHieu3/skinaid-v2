"""
Audit Service for Model Lifecycle Logging (PBI-27).

Centralized service for logging model lifecycle events to audit trail.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.modules.ai.models.audit_log import ModelAuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for managing model audit logs.
    
    Provides:
    - Log creation for all lifecycle events
    - Log querying and filtering
    - Audit trail export
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        action: str,
        resource_id: UUID,
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        resource_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> ModelAuditLog:
        """
        Log an action to the audit trail.
        
        Args:
            action: Action performed (model_upload, model_activate, etc.)
            resource_id: Affected resource ID
            actor_id: User who performed action
            actor_email: Actor's email
            actor_ip: Actor's IP address
            resource_version: Version affected
            details: Additional details
            status: Action status (success, failure, partial)
            error_message: Error message if failed
            error_code: Error code if failed
            
        Returns:
            Created audit log entry
        """
        log_entry = ModelAuditLog.create_log(
            action=action,
            resource_id=resource_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=resource_version,
            details=details,
            status=status,
            error_message=error_message,
            error_code=error_code
        )
        
        self.db.add(log_entry)
        await self.db.flush()
        await self.db.refresh(log_entry)
        
        logger.info(f"Audit log created: {action} on {resource_id} by {actor_id} - {status}")
        
        return log_entry
    
    async def log_upload(
        self,
        model_id: UUID,
        version_tag: str,
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
        is_beta: bool = False,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> ModelAuditLog:
        """Log a model upload event."""
        return await self.log_action(
            action="model_upload",
            resource_id=model_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=version_tag,
            details={
                "file_size": file_size,
                "file_hash": file_hash,
                "is_beta": is_beta
            },
            status=status,
            error_message=error_message
        )
    
    async def log_activate(
        self,
        model_id: UUID,
        version_tag: str,
        previous_version: Optional[str],
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> ModelAuditLog:
        """Log a model activation event."""
        return await self.log_action(
            action="model_activate",
            resource_id=model_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=version_tag,
            details={
                "previous_version": previous_version
            },
            status=status,
            error_message=error_message
        )
    
    async def log_rollback(
        self,
        model_id: UUID,
        from_version: str,
        to_version: str,
        reason: Optional[str],
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> ModelAuditLog:
        """Log a model rollback event."""
        return await self.log_action(
            action="model_rollback",
            resource_id=model_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=to_version,
            details={
                "from_version": from_version,
                "reason": reason
            },
            status=status,
            error_message=error_message
        )
    
    async def log_delete(
        self,
        model_id: UUID,
        version_tag: str,
        reason: Optional[str],
        is_permanent: bool = False,
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> ModelAuditLog:
        """Log a model deletion event."""
        return await self.log_action(
            action="model_delete",
            resource_id=model_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=version_tag,
            details={
                "reason": reason,
                "is_permanent": is_permanent
            },
            status=status,
            error_message=error_message
        )
    
    async def log_reload(
        self,
        model_type: str,
        from_version: str,
        to_version: str,
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> ModelAuditLog:
        """Log a model reload event."""
        return await self.log_action(
            action="model_reload",
            resource_id=model_type,  # Using model_type as resource_id for reload
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=to_version,
            details={
                "from_version": from_version
            },
            status=status,
            error_message=error_message
        )
    
    async def log_validation_failed(
        self,
        model_type: str,
        version_tag: str,
        error_code: str,
        error_message: str,
        actor_id: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> ModelAuditLog:
        """Log a validation failure event."""
        return await self.log_action(
            action="validation_failed",
            resource_id=model_type,
            actor_id=actor_id,
            actor_ip=actor_ip,
            resource_version=version_tag,
            details={
                "error_code": error_code
            },
            status="failure",
            error_message=error_message,
            error_code=error_code
        )
    
    async def get_logs(
        self,
        resource_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelAuditLog]:
        """
        Query audit logs with filters.
        
        Args:
            resource_id: Filter by resource ID
            actor_id: Filter by actor ID
            action: Filter by action type
            status: Filter by status
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of audit logs
        """
        query = select(ModelAuditLog)
        
        if resource_id:
            query = query.where(ModelAuditLog.resource_id == resource_id)
        if actor_id:
            query = query.where(ModelAuditLog.actor_id == actor_id)
        if action:
            query = query.where(ModelAuditLog.action == action)
        if status:
            query = query.where(ModelAuditLog.status == status)
        
        query = query.order_by(
            desc(ModelAuditLog.created_at)
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_logs_count(
        self,
        resource_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Get count of logs matching filters."""
        from sqlalchemy import func
        
        query = select(func.count()).select_from(ModelAuditLog)
        
        if resource_id:
            query = query.where(ModelAuditLog.resource_id == resource_id)
        if actor_id:
            query = query.where(ModelAuditLog.actor_id == actor_id)
        if action:
            query = query.where(ModelAuditLog.action == action)
        if status:
            query = query.where(ModelAuditLog.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
