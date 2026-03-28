"""
Audit Log Model for Model Lifecycle (PBI-27).

Dedicated audit log table for comprehensive model lifecycle tracking.
Complements the ModelVersionHistory with more detailed audit information.
"""

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4, UUID


class ModelAuditLog(SQLModel, table=True):
    """
    Audit log for AI model lifecycle events.
    
    Tracks all actions performed on models for compliance and debugging.
    """
    __tablename__ = "model_audit_logs"
    
    # Primary Key
    log_id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Action Information
    action: str = Field(
        max_length=50,
        index=True,
        description="Action performed: model_upload, model_activate, model_rollback, model_delete, model_reload, validation_failed"
    )
    resource_type: str = Field(
        default="ai_model",
        max_length=50,
        description="Type of resource affected"
    )
    resource_id: UUID = Field(
        ...,
        index=True,
        description="ID of the affected resource (model_id)"
    )
    resource_version: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Version tag affected"
    )
    
    # Actor Information
    actor_id: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        index=True,
        description="User ID who performed the action"
    )
    actor_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Email of the actor (denormalized for audit trail)"
    )
    actor_ip: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address of the actor"
    )
    actor_user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string"
    )
    
    # Action Details (stored as JSONB)
    details: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Detailed information about the action"
    )
    
    # Result Information
    status: str = Field(
        default="success",
        max_length=20,
        index=True,
        description="Action result: success, failure, partial"
    )
    error_message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message if action failed"
    )
    error_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Error code if action failed"
    )
    
    # Timestamp
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        index=True,
        description="Audit log creation timestamp"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_model_audit_action_resource", "action", "resource_id"),
        Index("ix_model_audit_actor", "actor_id", "created_at"),
        Index("ix_model_audit_status", "status"),
        Index("ix_model_audit_created_at", "created_at"),
    )
    
    @classmethod
    def create_log(
        cls,
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
    ) -> "ModelAuditLog":
        """
        Factory method to create an audit log entry.
        
        Args:
            action: Action performed
            resource_id: Affected resource ID
            actor_id: User who performed action
            actor_email: Actor's email
            actor_ip: Actor's IP address
            resource_version: Version affected
            details: Additional details
            status: Action status
            error_message: Error message if failed
            error_code: Error code if failed
            
        Returns:
            New ModelAuditLog instance
        """
        return cls(
            action=action,
            resource_id=resource_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            resource_version=resource_version,
            details=details or {},
            status=status,
            error_message=error_message,
            error_code=error_code
        )
