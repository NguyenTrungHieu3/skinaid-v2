"""
Model Service for AI Model Lifecycle Management (PBI-27).

Provides business logic for model operations:
- Upload new models
- List and query models
- Activate/deactivate versions
- Rollback to previous versions
- Soft delete and restore
- Metadata and metrics management
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.schemas.model_schemas import (
    ModelUploadRequest,
    ModelUploadResponse,
    ModelUploadRequest,
    ModelUploadResponse,
    ModelListResponse,
    ModelListFilters,
    ModelInfo,
    ModelVersionInfo,
    ModelDetailResponse,
    ModelVersionDetailResponse,
    ModelActivateRequest,
    ModelListFilters,
    ModelInfo,
    ModelVersionInfo,
    ModelDetailResponse,
    ModelVersionDetailResponse,
    ModelActivateRequest,
    ModelActivateResponse,
    ModelRollbackRequest,
    ModelRollbackResponse,
    ModelDeleteRequest,
    ModelDeleteResponse,
    ModelMetadataResponse,
    ModelMetrics,
    ModelRollbackRequest,
    ModelRollbackResponse,
    ModelDeleteRequest,
    ModelDeleteResponse,
    ModelMetadataResponse,
    ModelMetrics,
)
from app.modules.ai.repository.model_repository import ModelRepository
from app.modules.ai.services.model_validator import ModelValidator
from app.modules.ai.services.model_storage_service import ModelStorageService, get_storage_service
from app.modules.ai.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ModelServiceError(Exception):
    """Custom exception for model service errors."""
    
    def __init__(self, message: str, error_code: str = "SERVICE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ModelServiceError(Exception):
    """Custom exception for model service errors."""
    
    def __init__(self, message: str, error_code: str = "SERVICE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ModelService:
    """
    Service for managing AI model lifecycle.
    
    Operations:
    - Upload: Validate and store new model versions
    - List: Query models with filters and pagination
    - Detail: Get complete model information
    - Activate: Set a model version as active
    - Rollback: Revert to a previous version
    - Delete: Soft-delete model versions
    - Metadata: Update model metadata and metrics
    """
    
    def __init__(
        self, 
        db: AsyncSession,
        storage_service: Optional[ModelStorageService] = None
    ):
        self.db = db
        self.repository = ModelRepository(db)
        self.storage = storage_service or get_storage_service()
        self.audit_service = AuditService(db)
    
    # ============== Upload Operations ==============
    
    async def upload_model(
        self,
        upload_file,
        request: ModelUploadRequest,
        uploaded_by: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> ModelUploadResponse:
        """
        Upload a new model version.

        Args:
            upload_file: Uploaded file object
            request: Upload request data
            uploaded_by: User ID performing upload
            actor_ip: IP address of uploader

        Returns:
            Upload response with model info

        Raises:
            ModelServiceError: If upload fails
        """
        try:
            logger.info(f"Starting model upload: {request.model_type} v{request.version_tag}")

            # Step 1: Validate file and metadata
            validation_result = await ModelValidator.validate_all(
                file=upload_file,
                model_type=request.model_type,
                version_tag=request.version_tag
            )

            logger.info(f"Validation passed: {validation_result['file_size']} bytes, hash: {validation_result['file_hash']}")

            # Step 2: Check for duplicate version tag within this model type
            existing = await self.repository.get_model_by_version_tag(request.version_tag)
            if existing and existing.model_type == request.model_type:
                raise ModelServiceError(
                    f"Version tag '{request.version_tag}' already exists for model type '{request.model_type}'",
                    error_code="DUPLICATE_VERSION"
                )

            # FIXED: Generate model_id first before storing file
            # Each model version gets a unique UUID
            from uuid import uuid4
            new_model_id = uuid4()

            # Step 3: Store file using the storage service's upload method
            # FIXED: Use store_model_from_upload which handles file reading internally
            # This avoids double-reading the file after validation consumed it
            file_path, file_size = await self.storage.store_model_from_upload(
                upload_file=upload_file,
                model_type=request.model_type,
                model_id=new_model_id,
                version_tag=request.version_tag,
                file_hash=validation_result['file_hash']
            )

            logger.info(f"File stored at: {file_path}")

            # Step 4: Create database record
            model = await self.repository.create_model(
                model_type=request.model_type,
                version_tag=request.version_tag,
                file_path=file_path,
                file_size_bytes=file_size,
                file_hash=validation_result['file_hash'],
                description=request.description,
                metrics=request.metrics.model_dump() if request.metrics else None,
                is_beta=False,  # Beta flag removed
                created_by=uploaded_by,
                model_id=new_model_id  # FIXED: Pass the same UUID used for file storage
            )

            # Step 5: Log version change
            await self.repository.log_version_change(
                model_id=model.model_id,
                action="model_upload",
                to_version=request.version_tag,
                actor_id=uploaded_by,
                actor_ip=actor_ip,
                details={
                    "file_size": file_size,
                    "file_hash": validation_result['file_hash']
                }
            )

            logger.info(f"Model uploaded successfully: {model.model_id}")

            return ModelUploadResponse(
                success=True,
                model_id=model.model_id,
                version_id=model.model_id,  # Using model_id as version_id for simplicity
                version_tag=request.version_tag,
                file_size_bytes=file_size,
                file_path=file_path,
                uploaded_at=model.created_at,
                message=f"Model {request.model_type} v{request.version_tag} uploaded successfully"
            )

        except ModelServiceError:
            raise
        except Exception as e:
            logger.error(f"Model upload failed: {e}")
            raise ModelServiceError(
                f"Upload failed: {str(e)}",
                error_code="UPLOAD_FAILED"
            )
    
    # ============== List Operations ==============
    
    async def list_models(self, filters: Optional[ModelListFilters] = None) -> ModelListResponse:
        """
        List models with filtering and pagination.
        
        Args:
            filters: Optional filter criteria
            
        List models with filtering and pagination.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            List of models with metadata
        """
        filters = filters or ModelListFilters()
        
        # Get models from repository
        models, total = await self.repository.get_all_models(
            skip=0,
            limit=100,
            model_type=filters.model_type,
            status=filters.status,
            include_beta=filters.include_beta,
            include_deleted=False,
            search=filters.search
        )
        
        # Convert to response format
        model_infos = []
        for model in models:
            # Get version count for this model group
            versions = await self.repository.get_model_versions(model.model_id)

            # Get active version
            active_model = await self.repository.get_active_model(model.model_type)

            model_info = ModelInfo(
                model_id=model.model_id,
                model_type=model.model_type,
                name=model.name or f"{model.model_type} - {model.version_tag}",
                description=model.description,
                current_version=active_model.version_tag if active_model else None,
                version_tag=model.version_tag,
                is_active=model.is_active,  # Add is_active field for THIS model
                total_versions=len(versions),
                created_at=model.created_at,
                updated_at=model.updated_at,
                metrics=ModelMetrics(**model.metrics) if model.metrics else None
            )
            model_infos.append(model_info)
        
        # Get active version for display
        active_version = None
        if filters.model_type:
            active_model = await self.repository.get_active_model(filters.model_type)
            if active_model:
                active_version = active_model.version_tag
        
        return ModelListResponse(
            models=model_infos,
            active_version=active_version,
            total=total,
            filters_applied=filters
        )
    
    async def get_model_versions(self, model_id: UUID) -> dict:
        """
        Get all versions of a specific model.
        
        Args:
            model_id: Model UUID
            
        Returns:
            Dictionary with model versions
        """
        # Get model info
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")
        
        # Get all versions
        versions = await self.repository.get_model_versions(model_id)
        
        # Get active version
        active_version = await self.repository.get_active_model(model.model_type)
        
        version_infos = [
            ModelVersionInfo(
                version_id=v.model_id,
                model_id=v.model_id,
                version_tag=v.version_tag,
                version_number=v.version_number,
                is_active=v.is_active,
                is_beta=v.is_beta,
                created_at=v.created_at,
                deployed_at=v.deployed_at,
                deployed_by=v.deployed_by,
                metrics=ModelMetrics(**v.metrics) if v.metrics else None
            )
            for v in versions
        ]
        
        return {
            "model_id": model_id,
            "model_type": model.model_type,
            "versions": version_infos,
            "active_version": ModelVersionInfo(
                version_id=active_version.model_id,
                model_id=active_version.model_id,
                version_tag=active_version.version_tag,
                version_number=active_version.version_number,
                is_active=active_version.is_active,
                is_beta=active_version.is_beta,
                created_at=active_version.created_at,
                deployed_at=active_version.deployed_at,
                deployed_by=active_version.deployed_by,
                metrics=ModelMetrics(**active_version.metrics) if active_version.metrics else None
            ) if active_version else None,
            "total": len(versions)
        }
    
    # ============== Detail Operations ==============
    
    async def get_model_detail(self, model_id: UUID) -> ModelDetailResponse:
        """
        Get detailed model information.
        
        Args:
            model_id: Model UUID
            
            model_id: Model UUID
            
        Returns:
            Complete model details
        """
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")
        
        versions = await self.repository.get_model_versions(model_id)
        active_version = await self.repository.get_active_model(model.model_type)
        history = await self.repository.get_version_history(model_id, limit=20)
        
        return ModelDetailResponse(
            model=ModelInfo(
                model_id=model.model_id,
                model_type=model.model_type,
                name=model.name or f"{model.model_type} - {model.version_tag}",
                description=model.description,
                current_version=active_version.version_tag if active_version else None,
                version_tag=model.version_tag,
                total_versions=len(versions),
                created_at=model.created_at,
                updated_at=model.updated_at,
                created_by=model.created_by,
                metrics=ModelMetrics(**model.metrics) if model.metrics else None
            ),
            versions=[
                ModelVersionInfo(
                    version_id=v.model_id,
                    model_id=v.model_id,
                    version_tag=v.version_tag,
                    version_number=v.version_number,
                    is_active=v.is_active,
                    is_beta=v.is_beta,
                    created_at=v.created_at,
                    deployed_at=v.deployed_at,
                    deployed_by=v.deployed_by,
                    metrics=ModelMetrics(**v.metrics) if v.metrics else None
                )
                for v in versions
            ],
            active_version=ModelVersionInfo(
                version_id=active_version.model_id,
                model_id=active_version.model_id,
                version_tag=active_version.version_tag,
                version_number=active_version.version_number,
                is_active=active_version.is_active,
                is_beta=active_version.is_beta,
                created_at=active_version.created_at,
                deployed_at=active_version.deployed_at,
                deployed_by=active_version.deployed_by,
                metrics=ModelMetrics(**active_version.metrics) if active_version.metrics else None
            ) if active_version else None,
            version_history=[
                {
                    "action": h.action,
                    "from_version": h.from_version,
                    "to_version": h.to_version,
                    "actor_id": h.actor_id,
                    "timestamp": h.created_at,
                    "details": h.details
                }
                for h in history
            ]
        )
    
    # ============== Activate Operations ==============

    async def activate_model(
        self,
        model_id: UUID,
        request: Optional[ModelActivateRequest] = None,
        activated_by: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> ModelActivateResponse:
        """
        Activate a model version.

        Args:
            model_id: Model to activate
            request: Optional activation request
            activated_by: User ID performing activation
            actor_ip: IP address of activator

        Returns:
            Activation response
        """
        # Get model
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")

        if model.is_deleted:
            raise ModelServiceError("Cannot activate a deleted model", "MODEL_DELETED")

        # Get previous active version
        previous_active = await self.repository.get_active_model(model.model_type)
        previous_version = previous_active.version_tag if previous_active else None

        # Activate model (repository handles deactivating others)
        activated_model = await self.repository.activate_model(model_id, activated_by)

        # Log version change
        await self.repository.log_version_change(
            model_id=model_id,
            action="model_activate",
            from_version=previous_version,
            to_version=model.version_tag,
            actor_id=activated_by,
            actor_ip=actor_ip,
            details={
                "force": request.force if request else False,
                "previous_version": previous_version
            }
        )

        logger.info(f"Model activated: {model.model_type} v{model.version_tag}")

        return ModelActivateResponse(
            success=True,
            active_version=model.version_tag,
            previous_version=previous_version,
            activated_at=activated_model.deployed_at,
            model_id=model_id,
            message=f"Activated {model.model_type} v{model.version_tag}"
        )

    async def deactivate_model(
        self,
        model_id: UUID,
        deactivated_by: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> dict:
        """
        Deactivate a model version.

        RULE: Cannot deactivate the last active model of a type.

        Args:
            model_id: Model to deactivate
            deactivated_by: User ID performing deactivation
            actor_ip: IP address of deactivator

        Returns:
            Deactivation result dict

        Raises:
            ModelServiceError: If this is the only active model of its type
        """
        # Get model
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")

        if not model.is_active:
            raise ModelServiceError("Model is not active", "MODEL_NOT_ACTIVE")

        # RULE: Cannot deactivate the last active model of a type
        if await self.repository.is_only_active_model(model_id):
            raise ModelServiceError(
                f"Cannot deactivate: this is the only active model for type '{model.model_type}'. Activate another version first.",
                error_code="CANNOT_DEACTIVATE_LAST_ACTIVE"
            )

        # Store info for response
        version_tag = model.version_tag
        model_type = model.model_type

        # Deactivate the model
        model.is_active = False
        model.deployed_at = None
        model.activated_at = None
        model.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await self.db.flush()
        await self.db.refresh(model)

        # Log version change
        await self.repository.log_version_change(
            model_id=model_id,
            action="model_deactivate",
            from_version=version_tag,
            actor_id=deactivated_by,
            actor_ip=actor_ip,
            details={
                "reason": "Manual deactivation",
                "previous_status": "active"
            }
        )

        logger.info(f"Model deactivated: {model_type} v{version_tag}")

        return {
            "model_id": str(model_id),
            "version_tag": version_tag,
            "model_type": model_type,
            "deactivated_at": model.updated_at.isoformat(),
            "previous_status": "active",
            "current_status": "inactive"
        }

    async def rollback_model_type(
        self,
        model_type: str,
        rolled_back_by: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> ModelRollbackResponse:
        """
        Rollback a model type to its previously active version.

        RULE: Rollback is a TYPE-level operation, not per-version.

        Args:
            model_type: Model type to rollback
            rolled_back_by: User ID performing rollback
            actor_ip: IP address of rollback performer

        Returns:
            Rollback response

        Raises:
            ModelServiceError: If no previous version exists
        """
        # Get current active model
        current_active = await self.repository.get_active_model(model_type)
        if not current_active:
            raise ModelServiceError(
                f"No active model found for type '{model_type}'",
                "NO_ACTIVE_MODEL"
            )

        # Check if there's a previous version to roll back to
        if not current_active.previously_active_version_id:
            raise ModelServiceError(
                f"No previous version available for rollback of type '{model_type}'",
                "NO_PREVIOUS_VERSION"
            )

        # Get the previous version info for logging
        previous_version_model = await self.repository.get_by_id(current_active.previously_active_version_id)
        if not previous_version_model or previous_version_model.is_deleted:
            raise ModelServiceError(
                "Previous version not found or deleted",
                "PREVIOUS_VERSION_NOT_FOUND"
            )

        previous_version_tag = previous_version_model.version_tag
        current_version_tag = current_active.version_tag

        # Perform rollback (repository handles the activation)
        rolled_back_model = await self.repository.rollback_model_type(model_type, rolled_back_by)
        if not rolled_back_model:
            raise ModelServiceError(
                "Rollback failed",
                "ROLLBACK_FAILED"
            )

        # Log version change
        await self.repository.log_version_change(
            model_id=rolled_back_model.model_id,
            action="model_rollback",
            from_version=current_version_tag,
            to_version=previous_version_tag,
            actor_id=rolled_back_by,
            actor_ip=actor_ip,
            details={
                "model_type": model_type,
                "rollback_type": "type_level"
            }
        )

        logger.info(f"Model type '{model_type}' rolled back: {current_version_tag} -> {previous_version_tag}")

        return ModelRollbackResponse(
            success=True,
            previous_version=current_version_tag,
            rolled_back_version=previous_version_tag,
            rolled_back_at=rolled_back_model.deployed_at,
            model_id=rolled_back_model.model_id,
            message=f"Rolled back {model_type} from {current_version_tag} to {previous_version_tag}"
        )
    
    # ============== Rollback Operations ==============
    
    async def rollback_model(
        self,
        model_id: UUID,
        request: Optional[ModelRollbackRequest] = None,
        rolled_back_by: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> ModelRollbackResponse:
        """
        Rollback to a previous model version.
        
        Args:
            model_id: Model to rollback (or use model_type in request)
            request: Rollback request with target version
            rolled_back_by: User ID performing rollback
            actor_ip: IP address of rollback performer
            
        Returns:
            Rollback response
        """
        # Get current model
        current_model = await self.repository.get_model_by_id(model_id)
        if not current_model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")
        
        # Determine target version
        if request and request.target_version:
            # Find specific version
            target_model = await self.repository.get_model_by_version_tag(request.target_version)
            if not target_model:
                raise ModelServiceError(
                    f"Target version '{request.target_version}' not found",
                    "VERSION_NOT_FOUND"
                )
        else:
            # Find previous version (one before current)
            versions = await self.repository.get_model_versions(current_model.model_id)
            if len(versions) < 2:
                raise ModelServiceError(
                    "No previous version to rollback to",
                    "NO_PREVIOUS_VERSION"
                )
            
            # Get second-to-last version
            target_model = versions[-2] if versions[-1].model_id == model_id else versions[-1]
        
        # Get previous active version for logging
        previous_version = current_model.version_tag
        
        # Activate target model
        activated_model = await self.repository.activate_model(target_model.model_id, rolled_back_by)
        
        # Log version change
        await self.repository.log_version_change(
            model_id=target_model.model_id,
            action="model_rollback",
            from_version=previous_version,
            to_version=target_model.version_tag,
            actor_id=rolled_back_by,
            actor_ip=actor_ip,
            details={
                "reason": request.reason if request and request.reason else None,
                "previous_version": previous_version,
                "rolled_back_from": model_id
            }
        )
        
        logger.info(f"Model rolled back: {previous_version} -> {target_model.version_tag}")
        
        return ModelRollbackResponse(
            success=True,
            previous_version=previous_version,
            rolled_back_version=target_model.version_tag,
            rolled_back_at=activated_model.deployed_at,
            model_id=target_model.model_id,
            message=f"Rolled back to v{target_model.version_tag}"
        )
    
    # ============== Delete Operations ==============
    
    async def delete_model(
        self,
        model_id: UUID,
        request: Optional[ModelDeleteRequest] = None,
        deleted_by: Optional[UUID] = None,
        actor_ip: Optional[str] = None
    ) -> ModelDeleteResponse:
        """
        Soft-delete a model version.
        
        Args:
            model_id: Model to delete
            request: Delete request options
            deleted_by: User ID performing deletion
            actor_ip: IP address of deleter
            
        Returns:
            Delete response
        """
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")
        
        # Prevent deleting active model
        if model.is_active:
            raise ModelServiceError(
                "Cannot delete an active model. Deactivate it first.",
                "CANNOT_DELETE_ACTIVE"
            )
        
        # Store version tag for response
        deleted_version = model.version_tag
        
        # Soft delete in database
        deleted_model = await self.repository.soft_delete_model(model_id, deleted_by)
        
        # Note: We don't delete the actual file, just mark as deleted
        # Files can be cleaned up later by a maintenance job
        
        # Log version change
        await self.repository.log_version_change(
            model_id=model_id,
            action="model_delete",
            from_version=deleted_version,
            actor_id=deleted_by,
            actor_ip=actor_ip,
            details={
                "reason": request.reason if request and request.reason else None,
                "is_permanent": request.permanent if request else False
            }
        )
        
        logger.info(f"Model soft-deleted: {model_id} v{deleted_version}")
        
        return ModelDeleteResponse(
            success=True,
            deleted_version=deleted_version,
            deleted_at=deleted_model.deleted_at,
            is_permanent=request.permanent if request else False,
            message=f"Model v{deleted_version} deleted successfully"
        )
    
    # ============== Metadata Operations ==============
    
    async def get_model_metadata(self, model_id: UUID) -> ModelMetadataResponse:
        """
        Get model metadata.
        
        Args:
            model_id: Model UUID
            
        Returns:
            Model metadata
        """
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")
        
        return ModelMetadataResponse(
            model_id=model.model_id,
            version_tag=model.version_tag,
            description=model.description,
            is_beta=model.is_beta,
            metrics=ModelMetrics(**model.metrics) if model.metrics else None,
            file_info={
                "path": model.file_path,
                "size_bytes": model.file_size_bytes,
                "hash": model.file_hash
            },
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    async def update_model_metadata(
        self,
        model_id: UUID,
        description: Optional[str] = None,
        is_beta: Optional[bool] = None,
        metrics: Optional[ModelMetrics] = None,
        updated_by: Optional[UUID] = None
    ) -> ModelMetadataResponse:
        """
        Update model metadata.
        
        Args:
            model_id: Model to update
            description: New description
            is_beta: New beta status
            metrics: New metrics
            updated_by: User ID performing update
            
        Returns:
            Updated metadata
        """
        model = await self.repository.get_model_by_id(model_id)
        if not model:
            raise ModelServiceError(f"Model {model_id} not found", "MODEL_NOT_FOUND")
        
        # Update fields
        if description is not None:
            model.description = description
        if is_beta is not None:
            model.is_beta = is_beta
        if metrics is not None:
            await self.repository.update_model_metrics(model_id, metrics.model_dump())
        
        model.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()
        await self.db.refresh(model)
        
        return await self.get_model_metadata(model_id)
    
    # ============== Runtime Operations ==============
    
    async def get_runtime_status(self) -> dict:
        """
        Get runtime status of all models.
        
        Returns:
            Runtime status dictionary
        """
        # Get active models for each type
        model_types = ["detection", "classification", "segmentation", "severity_scoring"]
        
        status = {}
        for model_type in model_types:
            active_model = await self.repository.get_active_model(model_type)
            if active_model:
                status[model_type] = {
                    "loaded_version": active_model.version_tag,
                    "model_path": active_model.file_path,
                    "loaded_at": active_model.deployed_at,
                    "is_ready": True
                }
            else:
                status[model_type] = {
                    "loaded_version": None,
                    "model_path": None,
                    "loaded_at": None,
                    "is_ready": False
                }
        
        return status
