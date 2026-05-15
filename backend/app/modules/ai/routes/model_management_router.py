"""
Model Management Router (PBI-27).

Admin endpoints for AI model lifecycle management:
- Upload new models
- List and query models
- Activate/deactivate versions
- Rollback to previous versions
- Delete models (soft delete)
- View metadata and metrics
- Runtime status and reload
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Path, Query, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin, require_admin_or_moderator
from app.core.dependencies.database import get_db
from app.modules.users.models import User
from app.modules.ai.services.model_service import ModelService, ModelServiceError
from app.modules.ai.services.model_storage_service import get_storage_service
from app.modules.ai.schemas.model_schemas import (
    ModelUploadRequest,
    ModelUploadResponse,
    ModelListFilters,
    ModelListResponse,
    ModelDetailResponse,
    ModelActivateRequest,
    ModelActivateResponse,
    ModelRollbackRequest,
    ModelRollbackResponse,
    ModelDeleteRequest,
    ModelDeleteResponse,
    ModelMetadataResponse,
    ModelMetadataUpdate,
    ModelRuntimeHealthResponse,
    ModelReloadRequest,
    ModelReloadResponse,
    AuditLogListResponse,
)
from app.shared.response import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/models")


# ============== Helper Functions ==============

def get_model_service(db: AsyncSession) -> ModelService:
    """Get model service with dependencies."""
    return ModelService(db=db, storage_service=get_storage_service())


def get_actor_info(request: Request, current_user: User) -> tuple[Optional[UUID], Optional[str]]:
    """Extract actor information from request."""
    return current_user.user_id, request.client.host if request.client else None


# ============== Upload Operations ==============

@router.post(
    "/upload",
    response_model=SuccessResponse[ModelUploadResponse],
    summary="Upload new model version",
    description="Upload a new AI model version with validation",
)
async def upload_model(
    request: Request,
    file: UploadFile = File(..., description="Model file to upload"),
    model_type: str = Form(..., description="Model type: detection, classification, segmentation, severity_scoring"),
    version_tag: str = Form(..., description="Version tag (e.g., v1.0.0)"),
    description: Optional[str] = Form(None, description="Model description"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Upload a new AI model version.

    - **file**: Model file (.pt, .pth, .h5, .onnx, .safetensors)
    - **model_type**: Type of model
    - **version_tag**: Unique version identifier
    - **description**: Optional model description
    """
    try:
        # Build upload request (beta flag removed)
        upload_request = ModelUploadRequest(
            model_type=model_type,
            version_tag=version_tag,
            description=description,
            is_beta=False  # Beta flag removed
        )

        # Get actor info
        actor_id, actor_ip = get_actor_info(request, current_user)

        # Upload model
        service = get_model_service(db)
        result = await service.upload_model(
            upload_file=file,
            request=upload_request,
            uploaded_by=actor_id,
            actor_ip=actor_ip
        )

        return SuccessResponse(
            message="Model uploaded successfully",
            data=result,
        )

    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== List Operations ==============

@router.get(
    "",
    response_model=SuccessResponse[ModelListResponse],
    summary="List all models",
    description="Get list of all AI models with filtering",
)
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query("all", description="Filter by status: active, inactive, deprecated, all"),
    include_beta: bool = Query(True, description="Include beta versions"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    List all AI models with optional filtering.
    """
    filters = ModelListFilters(
        model_type=model_type,
        status=status,
        include_beta=include_beta,
        search=search
    )
    
    service = get_model_service(db)
    result = await service.list_models(filters)
    
    return SuccessResponse(
        message="Models retrieved successfully",
        data=result,
    )


@router.get(
    "/{model_id}",
    response_model=SuccessResponse[ModelDetailResponse],
    summary="Get model details",
    description="Get detailed information about a specific model",
)
async def get_model_detail(
    model_id: UUID = Path(..., description="Model UUID"),
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Get detailed information about a specific model including all versions.
    """
    service = get_model_service(db)
    try:
        result = await service.get_model_detail(model_id)
    except ModelServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return SuccessResponse(
        message="Model details retrieved successfully",
        data=result,
    )


@router.get(
    "/{model_id}/versions",
    response_model=SuccessResponse[dict],
    summary="Get model versions",
    description="Get all versions of a specific model",
)
async def get_model_versions(
    model_id: UUID = Path(..., description="Model UUID"),
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Get all versions of a specific model.
    """
    service = get_model_service(db)
    result = await service.get_model_versions(model_id)
    
    return SuccessResponse(
        message="Model versions retrieved successfully",
        data=result,
    )


# ============== Activate Operations ==============

@router.post(
    "/{model_id}/activate",
    response_model=SuccessResponse[ModelActivateResponse],
    summary="Activate model version",
    description="Activate a specific model version",
)
async def activate_model(
    request: Request,
    model_id: UUID = Path(..., description="Model UUID to activate"),
    force: bool = Query(False, description="Force activate even if validation fails"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Activate a specific AI model version.

    This will deactivate any currently active model of the same type.
    """
    try:
        actor_id, actor_ip = get_actor_info(request, current_user)

        service = get_model_service(db)
        result = await service.activate_model(
            model_id=model_id,
            request=ModelActivateRequest(force=force),
            activated_by=actor_id,
            actor_ip=actor_ip
        )

        return SuccessResponse(
            message="Model activated successfully",
            data=result,
        )

    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== Deactivate Operations ==============

@router.post(
    "/{model_id}/deactivate",
    response_model=SuccessResponse[dict],
    summary="Deactivate model version",
    description="Deactivate a currently active model version",
)
async def deactivate_model(
    request: Request,
    model_id: UUID = Path(..., description="Model UUID to deactivate"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Deactivate a currently active AI model version.

    RULE: Cannot deactivate the last active model of a type.
    """
    try:
        # Get model
        service = get_model_service(db)
        
        # Use the new service method that enforces the "last active" rule
        actor_id, actor_ip = get_actor_info(request, current_user)
        result = await service.deactivate_model(
            model_id=model_id,
            deactivated_by=actor_id,
            actor_ip=actor_ip
        )

        return SuccessResponse(
            message="Model deactivated successfully",
            data=result,
        )

    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== Rollback Operations (TYPE-LEVEL) ==============

@router.post(
    "/types/{model_type}/rollback",
    response_model=SuccessResponse[ModelRollbackResponse],
    summary="Rollback model type to previous version",
    description="Rollback a model type to its previously active version",
)
async def rollback_model_type(
    request: Request,
    model_type: str = Path(..., description="Model type to rollback (detection, classification, etc.)"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Rollback a model type to its previously active version.

    This is a TYPE-level operation, not per-version.
    It reverts the active version to the one that was active before.
    """
    try:
        actor_id, actor_ip = get_actor_info(request, current_user)

        service = get_model_service(db)
        result = await service.rollback_model_type(
            model_type=model_type,
            rolled_back_by=actor_id,
            actor_ip=actor_ip
        )

        return SuccessResponse(
            message="Model rolled back successfully",
            data=result,
        )

    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== Rollback Operations ==============

@router.post(
    "/{model_id}/rollback",
    response_model=SuccessResponse[ModelRollbackResponse],
    summary="Rollback model version",
    description="Rollback to a previous model version",
)
async def rollback_model(
    request: Request,
    model_id: UUID = Path(..., description="Current model UUID"),
    target_version: Optional[str] = Query(None, description="Specific version to rollback to"),
    reason: Optional[str] = Query(None, description="Reason for rollback"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Rollback to a previous model version.
    
    If target_version is not specified, rolls back to the previous version.
    """
    try:
        actor_id, actor_ip = get_actor_info(request, current_user)
        
        service = get_model_service(db)
        result = await service.rollback_model(
            model_id=model_id,
            request=ModelRollbackRequest(
                target_version=target_version,
                reason=reason
            ),
            rolled_back_by=actor_id,
            actor_ip=actor_ip
        )
        
        return SuccessResponse(
            message="Model rolled back successfully",
            data=result,
        )
        
    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== Delete Operations ==============

@router.delete(
    "/{model_id}",
    response_model=SuccessResponse[ModelDeleteResponse],
    summary="Delete model version",
    description="Soft-delete a model version",
)
async def delete_model(
    request: Request,
    model_id: UUID = Path(..., description="Model UUID to delete"),
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Soft-delete a model version.
    
    Note: Cannot delete active models. Deactivate first.
    """
    try:
        actor_id, actor_ip = get_actor_info(request, current_user)
        
        service = get_model_service(db)
        result = await service.delete_model(
            model_id=model_id,
            request=ModelDeleteRequest(reason=reason),
            deleted_by=actor_id,
            actor_ip=actor_ip
        )
        
        return SuccessResponse(
            message="Model deleted successfully",
            data=result,
        )
        
    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== Metadata Operations ==============

@router.get(
    "/{model_id}/metadata",
    response_model=SuccessResponse[ModelMetadataResponse],
    summary="Get model metadata",
    description="Get metadata for a specific model",
)
async def get_model_metadata(
    model_id: UUID = Path(..., description="Model UUID"),
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Get metadata for a specific model including description, metrics, and file info.
    """
    service = get_model_service(db)
    result = await service.get_model_metadata(model_id)
    
    return SuccessResponse(
        message="Model metadata retrieved successfully",
        data=result,
    )


@router.put(
    "/{model_id}/metadata",
    response_model=SuccessResponse[ModelMetadataResponse],
    summary="Update model metadata",
    description="Update metadata for a specific model",
)
async def update_model_metadata(
    model_id: UUID = Path(..., description="Model UUID"),
    description: Optional[str] = Body(None, description="Updated description"),
    is_beta: Optional[bool] = Body(None, description="Updated beta status"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Update metadata for a specific model.
    """
    service = get_model_service(db)
    result = await service.update_model_metadata(
        model_id=model_id,
        description=description,
        is_beta=is_beta,
        updated_by=current_user.user_id
    )
    
    return SuccessResponse(
        message="Model metadata updated successfully",
        data=result,
    )


# ============== Runtime Operations ==============

@router.get(
    "/runtime/status",
    response_model=SuccessResponse[dict],
    summary="Get runtime status",
    description="Get runtime status of all loaded models",
)
async def get_runtime_status(
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Get runtime status of all loaded models.
    """
    service = get_model_service(db)
    result = await service.get_runtime_status()
    
    return SuccessResponse(
        message="Runtime status retrieved successfully",
        data=result,
    )


@router.post(
    "/runtime/reload",
    response_model=SuccessResponse[ModelReloadResponse],
    summary="Reload model at runtime",
    description="Reload a model type with the active version (internal API)",
)
async def reload_model(
    request: Request,
    model_type: str = Body(..., description="Model type to reload"),
    version_tag: Optional[str] = Body(None, description="Specific version to load"),
    api_key: str = Body(..., description="Internal API key for authentication"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Reload a model at runtime.
    
    This is an internal API that requires an API key.
    It triggers the AI/ML service to reload the model from disk.
    """
    from app.core.config import settings
    
    # Validate API key
    if api_key != settings.AI_API_KEY:
        return ErrorResponse(
            message="Invalid API key",
            error_code="INVALID_API_KEY",
            status_code=403
        )
    
    try:
        # Get active model for this type
        service = get_model_service(db)
        
        # For now, return a success response
        # In Phase 5, we'll integrate with the AI/ML service
        result = ModelReloadResponse(
            success=True,
            model_type=model_type,
            previous_version="unknown",  # Will be filled in Phase 5
            new_version=version_tag or "active",
            reloaded_at=datetime.now(timezone.utc),
            message=f"Model reload triggered for {model_type}"
        )
        
        return SuccessResponse(
            message="Model reload triggered successfully",
            data=result,
        )
        
    except ModelServiceError as e:
        return ErrorResponse(
            message=e.message,
            error_code=e.error_code,
            status_code=400
        )


# ============== Audit Log Operations ==============

@router.get(
    "/{model_id}/logs",
    response_model=SuccessResponse[AuditLogListResponse],
    summary="Get model audit logs",
    description="Get audit logs for a specific model",
)
async def get_model_logs(
    model_id: UUID = Path(..., description="Model UUID"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to retrieve"),
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Get audit logs for a specific model showing all lifecycle events.
    """
    from app.modules.ai.repository.model_repository import ModelRepository
    
    repository = ModelRepository(db)
    history = await repository.get_version_history(model_id, limit=limit)
    
    # Convert to audit log format
    logs = [
        {
            "log_id": h.history_id,
            "action": h.action,
            "resource_type": "ai_model",
            "resource_id": h.model_id,
            "actor_id": h.actor_id,
            "details": h.details,
            "timestamp": h.created_at,
            "ip_address": h.actor_ip
        }
        for h in history
    ]
    
    result = AuditLogListResponse(
        logs=logs,
        total=len(logs),
        filters_applied={"model_id": str(model_id), "limit": limit}
    )
    
    return SuccessResponse(
        message="Audit logs retrieved successfully",
        data=result,
    )
