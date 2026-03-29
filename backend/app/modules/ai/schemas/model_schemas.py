from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
import re


# ============== Base Model Info ==============

class ModelMetrics(BaseModel):
    """Performance metrics for a model version."""
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model accuracy score (0-1)")
    precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="Precision score")
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recall score")
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1 score")
    confusion_matrix: Optional[Dict[str, Any]] = Field(None, description="Confusion matrix data")
    additional_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom metrics")


class ModelVersionInfo(BaseModel):
    """Information about a specific model version."""
    version_id: UUID = Field(..., description="Unique version identifier")
    model_id: UUID = Field(..., description="Parent model identifier")
    version_tag: str = Field(..., description="Version tag (e.g., v1.0.0)")
    version_number: int = Field(..., description="Sequential version number")
    is_active: bool = Field(default=False, description="Whether this version is currently active")
    is_beta: bool = Field(default=False, description="Whether this is a beta version")
    created_at: datetime = Field(..., description="Version creation timestamp")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")
    deployed_by: Optional[UUID] = Field(None, description="User ID who deployed this version")
    metrics: Optional[ModelMetrics] = Field(None, description="Performance metrics")


class ModelInfo(BaseModel):
    """Complete information about an AI model."""
    model_id: UUID = Field(..., description="Unique model identifier")
    model_type: Literal["detection", "classification", "segmentation", "severity_scoring"] = Field(
        ..., description="Model type"
    )
    name: str = Field(..., description="Model display name")
    description: Optional[str] = Field(None, description="Model description")
    current_version: Optional[str] = Field(None, description="Currently active version tag for this model type")
    version_tag: Optional[str] = Field(None, description="Version tag of THIS specific model version")
    is_active: bool = Field(default=False, description="Whether THIS specific model is active")
    total_versions: int = Field(0, description="Total number of versions")
    created_at: datetime = Field(..., description="Model creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[UUID] = Field(None, description="User ID who created the model")
    metrics: Optional[ModelMetrics] = Field(None, description="Current version metrics")


# ============== Upload Schemas ==============

class ModelUploadRequest(BaseModel):
    """Request schema for uploading a new model."""
    model_type: Literal["detection", "classification", "segmentation", "severity_scoring"] = Field(
        ..., description="Type of model"
    )
    version_tag: str = Field(..., min_length=1, max_length=50, description="Version tag (e.g., v1.0.0)")
    description: Optional[str] = Field(None, max_length=1000, description="Model description")
    is_beta: bool = Field(default=False, description="Mark as beta version")
    metrics: Optional[ModelMetrics] = Field(None, description="Initial performance metrics")
    
    @field_validator("version_tag")
    @classmethod
    def validate_version_tag(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Version tag can only contain letters, numbers, dots, hyphens, and underscores")
        if len(v) > 50:
            raise ValueError("Version tag must be 50 characters or less")
        return v


class ModelUploadResponse(BaseModel):
    """Response schema after successful model upload."""
    success: bool = Field(..., description="Whether upload was successful")
    model_id: UUID = Field(..., description="Created model ID")
    version_id: UUID = Field(..., description="Created version ID")
    version_tag: str = Field(..., description="Uploaded version tag")
    file_size_bytes: int = Field(..., description="Size of uploaded file")
    file_path: str = Field(..., description="Storage path of uploaded file")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    message: str = Field(..., description="Success message")


# ============== List & Query Schemas ==============

class ModelListFilters(BaseModel):
    """Filters for listing models."""
    model_type: Optional[Literal["detection", "classification", "segmentation", "severity_scoring"]] = Field(
        None, description="Filter by model type"
    )
    status: Optional[Literal["active", "inactive", "deprecated", "all"]] = Field(
        "all", description="Filter by activation status"
    )
    include_beta: bool = Field(default=True, description="Include beta versions")
    search: Optional[str] = Field(None, max_length=100, description="Search in name/description")


class ModelListResponse(BaseModel):
    """Response schema for listing models."""
    models: List[ModelInfo] = Field(default_factory=list, description="List of models")
    active_version: Optional[str] = Field(None, description="Currently active version tag")
    total: int = Field(0, description="Total number of models matching filters")
    filters_applied: ModelListFilters = Field(..., description="Filters that were applied")


class ModelVersionListResponse(BaseModel):
    """Response schema for listing model versions."""
    model_id: UUID = Field(..., description="Parent model ID")
    model_type: str = Field(..., description="Model type")
    versions: List[ModelVersionInfo] = Field(default_factory=list, description="List of versions")
    active_version: Optional[ModelVersionInfo] = Field(None, description="Currently active version")
    total: int = Field(0, description="Total number of versions")


# ============== Detail Schemas ==============

class ModelDetailResponse(BaseModel):
    """Detailed response for a single model."""
    model: ModelInfo = Field(..., description="Model information")
    versions: List[ModelVersionInfo] = Field(default_factory=list, description="All versions")
    active_version: Optional[ModelVersionInfo] = Field(None, description="Active version details")
    version_history: List[Dict[str, Any]] = Field(default_factory=list, description="Version change history")


class ModelVersionDetailResponse(BaseModel):
    """Detailed response for a single model version."""
    version: ModelVersionInfo = Field(..., description="Version information")
    model: ModelInfo = Field(..., description="Parent model information")
    file_info: Dict[str, Any] = Field(..., description="File storage information")
    metrics: Optional[ModelMetrics] = Field(None, description="Performance metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============== Activate/Rollback Schemas ==============

class ModelActivateRequest(BaseModel):
    """Request to activate a model version."""
    force: bool = Field(False, description="Force activate even if validation fails")
    activate_by: Optional[UUID] = Field(None, description="User ID performing activation")


class ModelActivateResponse(BaseModel):
    """Response after activating a model."""
    success: bool = Field(..., description="Whether activation was successful")
    active_version: str = Field(..., description="Newly activated version tag")
    previous_version: Optional[str] = Field(None, description="Previously active version tag")
    activated_at: datetime = Field(..., description="Activation timestamp")
    model_id: UUID = Field(..., description="Model ID")
    message: str = Field(..., description="Success message")


class ModelRollbackRequest(BaseModel):
    """Request to rollback to a previous version."""
    target_version: Optional[str] = Field(None, description="Specific version tag to rollback to")
    rollback_by: Optional[UUID] = Field(None, description="User ID performing rollback")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for rollback")


class ModelRollbackResponse(BaseModel):
    """Response after rollback operation."""
    success: bool = Field(..., description="Whether rollback was successful")
    previous_version: str = Field(..., description="Version rolled back from")
    rolled_back_version: str = Field(..., description="Version rolled back to")
    rolled_back_at: datetime = Field(..., description="Rollback timestamp")
    model_id: UUID = Field(..., description="Model ID")
    message: str = Field(..., description="Success message")


# ============== Delete Schemas ==============

class ModelDeleteRequest(BaseModel):
    """Request to soft-delete a model version."""
    delete_by: Optional[UUID] = Field(None, description="User ID performing deletion")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deletion")
    permanent: bool = Field(default=False, description="Permanently delete (admin only)")


class ModelDeleteResponse(BaseModel):
    """Response after deletion."""
    success: bool = Field(..., description="Whether deletion was successful")
    deleted_version: str = Field(..., description="Deleted version tag")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    is_permanent: bool = Field(..., description="Whether deletion was permanent")
    message: str = Field(..., description="Success message")


# ============== Metadata & Metrics Schemas ==============

class ModelMetadataUpdate(BaseModel):
    """Request to update model metadata."""
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    is_beta: Optional[bool] = Field(None, description="Update beta status")
    metrics: Optional[ModelMetrics] = Field(None, description="Updated metrics")
    updated_by: Optional[UUID] = Field(None, description="User ID performing update")


class ModelMetadataResponse(BaseModel):
    """Response with model metadata."""
    model_id: UUID = Field(..., description="Model ID")
    version_tag: str = Field(..., description="Version tag")
    description: Optional[str] = Field(None, description="Model description")
    is_beta: bool = Field(..., description="Beta status")
    metrics: Optional[ModelMetrics] = Field(None, description="Performance metrics")
    file_info: Dict[str, Any] = Field(..., description="File information")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ============== Runtime & Health Schemas ==============

class ModelRuntimeStatus(BaseModel):
    """Runtime status of loaded models."""
    model_type: str = Field(..., description="Model type")
    loaded_version: str = Field(..., description="Currently loaded version")
    model_path: str = Field(..., description="Path to loaded model file")
    loaded_at: datetime = Field(..., description="When model was loaded")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    is_ready: bool = Field(..., description="Whether model is ready for inference")
    last_inference_at: Optional[datetime] = Field(None, description="Last inference timestamp")


class ModelRuntimeHealthResponse(BaseModel):
    """Health status of all runtime models."""
    detection: Optional[ModelRuntimeStatus] = Field(None, description="Detection model status")
    classification: Optional[ModelRuntimeStatus] = Field(None, description="Classification model status")
    segmentation: Optional[ModelRuntimeStatus] = Field(None, description="Segmentation model status")
    severity_scoring: Optional[ModelRuntimeStatus] = Field(None, description="Severity scoring model status")
    overall_health: bool = Field(..., description="Overall system health")
    timestamp: datetime = Field(..., description="Health check timestamp")


class ModelReloadRequest(BaseModel):
    """Request to reload a model at runtime."""
    model_type: Literal["detection", "classification", "segmentation", "severity_scoring"] = Field(
        ..., description="Model type to reload"
    )
    version_tag: Optional[str] = Field(None, description="Specific version to load (uses active if not specified)")
    api_key: str = Field(..., description="Internal API key for authentication")


class ModelReloadResponse(BaseModel):
    """Response after model reload."""
    success: bool = Field(..., description="Whether reload was successful")
    model_type: str = Field(..., description="Model type that was reloaded")
    previous_version: str = Field(..., description="Previous loaded version")
    new_version: str = Field(..., description="Newly loaded version")
    reloaded_at: datetime = Field(..., description="Reload timestamp")
    message: str = Field(..., description="Success message")
    error_details: Optional[str] = Field(None, description="Error details if reload failed")


# ============== Audit Log Schemas ==============

class AuditLogEntry(BaseModel):
    """Audit log entry for model lifecycle events."""
    log_id: UUID = Field(..., description="Log entry ID")
    action: Literal[
        "model_upload",
        "model_activate",
        "model_rollback",
        "model_delete",
        "model_reload",
        "validation_failed"
    ] = Field(..., description="Action performed")
    resource_type: str = Field(default="ai_model", description="Resource type")
    resource_id: UUID = Field(..., description="Affected resource ID")
    actor_id: Optional[UUID] = Field(None, description="User ID who performed action")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action details")
    timestamp: datetime = Field(..., description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address of actor")


class AuditLogListResponse(BaseModel):
    """Response for audit log queries."""
    logs: List[AuditLogEntry] = Field(default_factory=list, description="List of audit logs")
    total: int = Field(0, description="Total number of logs")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
