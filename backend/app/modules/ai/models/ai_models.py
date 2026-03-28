from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID


class AIModel(SQLModel, table=True):
    """
    AI Model storage table (PBI-27).
    
    Supports model versioning, soft-delete, and lifecycle management.
    Each record represents a specific version of a model.
    """
    __tablename__ = "ai_models"
    
    # Primary Key
    model_id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Model Identification
    model_type: str = Field(
        max_length=50, 
        index=True,
        description="Model type: 'detection', 'classification', 'segmentation', 'severity_scoring'"
    )
    version_tag: str = Field(
        max_length=50, 
        index=True,
        description="Human-readable version tag (e.g., v1.0.0)"
    )
    version_number: int = Field(
        default=1,
        ge=1,
        description="Sequential version number for ordering"
    )
    
    # File Storage
    file_path: str = Field(
        ...,
        description="Path to stored model file"
    )
    file_size_bytes: Optional[float] = Field(
        default=None,
        ge=0,
        description="File size in bytes (stored as MB in old schema)"
    )
    file_hash: Optional[str] = Field(
        default=None,
        max_length=64,
        description="SHA-256 hash of file for integrity verification"
    )
    
    # Model Metadata
    name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Display name for the model"
    )
    description: Optional[str] = Field(
        default=None,
        description="Model description"
    )
    
    # Performance Metrics (stored as JSONB)
    metrics: dict = Field(
        default_factory=dict, 
        sa_column=Column(JSONB),
        description="Performance metrics (accuracy, precision, recall, etc.)"
    )
    
    # Status Flags
    is_active: bool = Field(
        default=False, 
        index=True,
        description="Whether this version is currently active"
    )
    is_beta: bool = Field(
        default=False,
        description="Whether this is a beta/experimental version"
    )
    is_deleted: bool = Field(
        default=False,
        index=True,
        description="Soft delete flag"
    )
    
    # Traffic Split (for A/B testing or canary deployments)
    traffic_percentage: int = Field(
        default=0, 
        ge=0, 
        le=100,
        description="Percentage of traffic routed to this model"
    )
    
    # Deployment Info
    deployed_at: Optional[datetime] = Field(
        default=None,
        description="When this model was deployed"
    )
    deployed_by: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        description="User ID who deployed this model"
    )
    
    # Activation Tracking (for rollback support)
    activated_at: Optional[datetime] = Field(
        default=None,
        index=True,
        description="When this version was activated"
    )
    previously_active_version_id: Optional[UUID] = Field(
        default=None,
        foreign_key="ai_models.model_id",
        description="ID of the previously active version (for rollback tracking)"
    )

    # Audit Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        index=True,
        description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Record last update timestamp"
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Soft delete timestamp"
    )
    deleted_by: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        description="User ID who deleted this model"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_ai_models_type_active", "model_type", "is_active"),
        Index("ix_ai_models_type_deleted", "model_type", "is_deleted"),
        Index("ix_ai_models_created_at", "created_at"),
        Index("ix_ai_models_deployed_at", "deployed_at"),
        Index("ix_ai_models_activated_at", "activated_at"),
        Index("ix_ai_models_prev_active", "previously_active_version_id"),
        Index("uq_ai_models_type_version", "model_type", "version_tag", unique=True),
    )

    def soft_delete(self, deleted_by: Optional[UUID] = None) -> None:
        """Mark this model as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.deleted_by = deleted_by
        # Deactivate if currently active
        if self.is_active:
            self.is_active = False
    
    def restore(self) -> None:
        """Restore a soft-deleted model."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    def activate(self, previously_active_id: Optional[UUID] = None) -> None:
        """Activate this model version."""
        self.is_active = True
        self.deployed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.activated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.previously_active_version_id = previously_active_id

    def deactivate(self) -> None:
        """Deactivate this model version."""
        self.is_active = False


class ModelVersionHistory(SQLModel, table=True):
    """
    Model version change history for audit trail.
    Tracks all version transitions and state changes.
    """
    __tablename__ = "model_version_history"
    
    history_id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: UUID = Field(
        foreign_key="ai_models.model_id", 
        index=True,
        description="Reference to the model"
    )
    
    # Action Information
    action: str = Field(
        max_length=50,
        index=True,
        description="Action performed: upload, activate, deactivate, rollback, delete, restore"
    )
    from_version: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Previous version tag (if applicable)"
    )
    to_version: Optional[str] = Field(
        default=None,
        max_length=50,
        description="New version tag (if applicable)"
    )
    
    # Actor Information
    actor_id: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        description="User ID who performed the action"
    )
    actor_ip: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address of the actor"
    )
    
    # Additional Details (stored as JSONB)
    details: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Additional details about the change"
    )
    
    # Timestamp
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        index=True,
        description="History record creation timestamp"
    )
    
    __table_args__ = (
        Index("ix_model_history_model_action", "model_id", "action"),
        Index("ix_model_history_created_at", "created_at"),
    )
