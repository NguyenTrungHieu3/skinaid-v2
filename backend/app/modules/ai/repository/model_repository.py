"""
Model Repository for AI Model Database Operations (PBI-27).

Provides database access layer for model lifecycle management:
- CRUD operations for AIModel and ModelVersionHistory
- Version queries and filtering
- Active model management
- Soft delete support
"""

from typing import List, Optional, Sequence, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, desc, asc, or_, and_, false, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.base_repository import BaseRepository
from app.modules.ai.models.ai_models import AIModel, ModelVersionHistory


class ModelRepository(BaseRepository[AIModel]):
    """
    Repository for AI model database operations.
    
    Handles:
    - Model and version CRUD
    - Version listing and filtering
    - Active model queries
    - Soft delete operations
    - Version history tracking
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(AIModel, db)
    
    # ============== Model Queries ==============
    
    async def get_model_by_id(
        self, 
        model_id: UUID,
        include_deleted: bool = False
    ) -> Optional[AIModel]:
        """
        Get a model by ID.
        
        Args:
            model_id: Model UUID
            include_deleted: Whether to include soft-deleted models
            
        Returns:
            Model if found, None otherwise
        """
        filters = [AIModel.model_id == model_id]
        if not include_deleted:
            filters.append(AIModel.is_deleted == false())
        
        return await self.get_one(*filters)
    
    async def get_model_by_version_tag(
        self,
        version_tag: str,
        include_deleted: bool = False
    ) -> Optional[AIModel]:
        """
        Get a model by version tag.
        
        Args:
            version_tag: Version tag string
            include_deleted: Whether to include soft-deleted models
            
        Returns:
            Model if found, None otherwise
        """
        filters = [AIModel.version_tag == version_tag]
        if not include_deleted:
            filters.append(AIModel.is_deleted == false())
        
        return await self.get_one(*filters)
    
    async def get_models_by_type(
        self,
        model_type: str,
        include_deleted: bool = False
    ) -> Sequence[AIModel]:
        """
        Get all models of a specific type.
        
        Args:
            model_type: Model type (detection, classification, etc.)
            include_deleted: Whether to include soft-deleted models
            
        Returns:
            List of models
        """
        filters = [AIModel.model_type == model_type.lower()]
        if not include_deleted:
            filters.append(AIModel.is_deleted == false())
        
        return await self.get_many(*filters, order_by=desc(AIModel.created_at))
    
    async def get_all_models(
        self,
        skip: int = 0,
        limit: int = 100,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        include_beta: bool = True,
        include_deleted: bool = False,
        search: Optional[str] = None
    ) -> Tuple[Sequence[AIModel], int]:
        """
        Get all models with filtering, pagination, and search.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            model_type: Filter by model type
            status: Filter by status (active, inactive, deprecated, all)
            include_beta: Whether to include beta versions
            include_deleted: Whether to include soft-deleted models
            search: Search term for name/description
            
        Returns:
            Tuple of (models list, total count)
        """
        # Build base filters
        filters = []
        if not include_deleted:
            filters.append(AIModel.is_deleted == false())
        
        if model_type:
            filters.append(AIModel.model_type == model_type.lower())
        
        if not include_beta:
            filters.append(AIModel.is_beta == false())
        
        if status and status.lower() != "all":
            if status.lower() == "active":
                filters.append(AIModel.is_active == True)
            elif status.lower() == "inactive":
                filters.append(AIModel.is_active == False)
            elif status.lower() == "deprecated":
                # Deprecated = old inactive versions
                filters.append(AIModel.is_active == False)
        
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    AIModel.name.ilike(search_pattern),
                    AIModel.description.ilike(search_pattern),
                    AIModel.version_tag.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(AIModel).where(*filters)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get models
        query = select(AIModel).where(*filters).order_by(
            desc(AIModel.created_at)
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return models, total
    
    async def get_active_model(self, model_type: str) -> Optional[AIModel]:
        """
        Get the currently active model for a specific type.
        
        Args:
            model_type: Model type to get active version for
            
        Returns:
            Active model if exists, None otherwise
        """
        return await self.get_one(
            AIModel.model_type == model_type.lower(),
            AIModel.is_active == True,
            AIModel.is_deleted == false()
        )
    
    async def get_active_model_version(model_type: str) -> Optional[str]:
        """
        Get the version tag of the active model.
        
        Args:
            model_type: Model type
            
        Returns:
            Version tag if active model exists, None otherwise
        """
        # This is a static method for convenience
        pass
    
    async def get_model_versions(
        self,
        model_id: UUID,
        include_deleted: bool = False
    ) -> Sequence[AIModel]:
        """
        Get all versions of a specific model.
        
        Args:
            model_id: Model UUID
            include_deleted: Whether to include soft-deleted versions
            
        Returns:
            List of model versions ordered by version number
        """
        filters = [AIModel.model_id == model_id]
        if not include_deleted:
            filters.append(AIModel.is_deleted == false())
        
        return await self.get_many(
            *filters,
            order_by=asc(AIModel.version_number)
        )
    
    async def get_latest_version_number(self, model_id: UUID) -> int:
        """
        Get the latest version number for a model.
        
        Args:
            model_id: Model UUID
            
        Returns:
            Latest version number, or 0 if no versions exist
        """
        query = select(func.max(AIModel.version_number)).where(
            AIModel.model_id == model_id
        )
        result = await self.db.execute(query)
        max_version = result.scalar()
        return max_version or 0
    
    # ============== Create/Update Operations ==============
    
    async def create_model(
        self,
        model_type: str,
        version_tag: str,
        file_path: str,
        file_size_bytes: int,
        file_hash: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        is_beta: bool = False,
        created_by: Optional[UUID] = None,
        model_id: Optional[UUID] = None
    ) -> AIModel:
        """
        Create a new model version.

        Args:
            model_type: Type of model
            version_tag: Version tag
            file_path: Path to stored model file
            file_size_bytes: File size in bytes
            file_hash: SHA-256 hash of file
            name: Display name
            description: Model description
            metrics: Performance metrics dict
            is_beta: Whether this is a beta version
            created_by: User ID who created the model
            model_id: Optional pre-generated UUID (for file path consistency)

        Returns:
            Created model
        """
        # FIXED: Use provided model_id if available, otherwise generate new one
        # This ensures consistency between file storage path and database record
        if model_id is None:
            import uuid
            model_id = uuid.uuid4()

        # Get next version number (based on model_type, not model_id)
        version_number = await self.get_latest_version_number_for_type(model_type) + 1

        # Create model
        model = AIModel(
            model_id=model_id,
            model_type=model_type.lower(),
            version_tag=version_tag,
            version_number=version_number,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            name=name,
            description=description,
            metrics=metrics or {},
            is_beta=is_beta,
            is_active=False,
            is_deleted=False,
            created_by=created_by
        )

        return await self.create(model)

    async def get_latest_version_number_for_type(self, model_type: str) -> int:
        """
        Get the latest version number for a model type.
        
        Args:
            model_type: Model type
            
        Returns:
            Latest version number, or 0 if no versions exist
        """
        query = select(func.max(AIModel.version_number)).where(
            AIModel.model_type == model_type.lower(),
            AIModel.is_deleted == false()
        )
        result = await self.db.execute(query)
        max_version = result.scalar()
        return max_version or 0
    async def activate_model(self, model_id: UUID, deployed_by: Optional[UUID] = None) -> AIModel:
        """
        Activate a model version.

        Args:
            model_id: Model to activate
            deployed_by: User ID performing activation

        Returns:
            Activated model
        """
        model = await self.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Get the currently active model of this type (to track for rollback)
        previous_active = await self.get_active_model(model.model_type)
        previous_active_id = previous_active.model_id if previous_active else None

        # Deactivate all models of the same type first
        await self.deactivate_models_by_type(model.model_type)

        # Activate this model, tracking the previous active version
        model.activate(previously_active_id=previous_active_id)
        if deployed_by:
            model.deployed_by = deployed_by

        await self.db.flush()
        await self.db.refresh(model)

        return model
    
    async def deactivate_models_by_type(self, model_type: str) -> int:
        """
        Deactivate all models of a specific type.

        Args:
            model_type: Model type to deactivate

        Returns:
            Number of models deactivated
        """
        stmt = update(AIModel).where(
            AIModel.model_type == model_type.lower(),
            AIModel.is_active == True
        ).values(
            is_active=False,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        result = await self.db.execute(stmt)
        await self.db.flush()

        return result.rowcount or 0

    async def is_only_active_model(self, model_id: UUID) -> bool:
        """
        Check if this model is the only active model of its type.

        Args:
            model_id: Model to check

        Returns:
            True if this is the only active model of its type
        """
        model = await self.get_by_id(model_id)
        if not model or not model.is_active:
            return False

        # Count other active models of the same type
        count_query = select(func.count()).where(
            AIModel.model_type == model.model_type,
            AIModel.is_active == True,
            AIModel.model_id != model_id,
            AIModel.is_deleted == false()
        )
        count_result = await self.db.execute(count_query)
        other_active_count = count_result.scalar() or 0

        return other_active_count == 0

    async def get_active_model_count_by_type(self, model_type: str) -> int:
        """
        Get count of active models for a specific type.

        Args:
            model_type: Model type

        Returns:
            Number of active models
        """
        count_query = select(func.count()).where(
            AIModel.model_type == model_type.lower(),
            AIModel.is_active == True,
            AIModel.is_deleted == false()
        )
        count_result = await self.db.execute(count_query)
        return count_result.scalar() or 0

    async def rollback_model_type(self, model_type: str, rolled_back_by: Optional[UUID] = None) -> Optional[AIModel]:
        """
        Rollback a model type to its previously active version.

        Args:
            model_type: Model type to rollback
            rolled_back_by: User ID performing rollback

        Returns:
            The newly activated model, or None if no previous version exists
        """
        # Get current active model
        current_active = await self.get_active_model(model_type)
        if not current_active:
            return None

        # Check if there's a previous active version to roll back to
        if not current_active.previously_active_version_id:
            return None

        # Get the previous active version
        previous_active = await self.get_by_id(current_active.previously_active_version_id)
        if not previous_active or previous_active.is_deleted:
            return None

        # Activate the previous version (this will set its previously_active to current)
        return await self.activate_model(previous_active.model_id, rolled_back_by)
    
    async def soft_delete_model(
        self, 
        model_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> AIModel:
        """
        Soft delete a model.
        
        Args:
            model_id: Model to delete
            deleted_by: User ID performing deletion
            
        Returns:
            Deleted model
        """
        model = await self.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        model.soft_delete(deleted_by)
        
        await self.db.flush()
        await self.db.refresh(model)
        
        return model
    
    async def restore_model(self, model_id: UUID) -> AIModel:
        """
        Restore a soft-deleted model.
        
        Args:
            model_id: Model to restore
            
        Returns:
            Restored model
        """
        model = await self.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        model.restore()
        
        await self.db.flush()
        await self.db.refresh(model)
        
        return model
    
    async def update_model_metrics(
        self,
        model_id: UUID,
        metrics: Dict[str, Any]
    ) -> AIModel:
        """
        Update model performance metrics.
        
        Args:
            model_id: Model to update
            metrics: New metrics dict
            
        Returns:
            Updated model
        """
        model = await self.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # Merge metrics
        current_metrics = model.metrics or {}
        current_metrics.update(metrics)
        model.metrics = current_metrics
        model.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await self.db.flush()
        await self.db.refresh(model)
        
        return model
    
    # ============== Version History ==============
    
    async def log_version_change(
        self,
        model_id: UUID,
        action: str,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        actor_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ModelVersionHistory:
        """
        Log a version change event.
        
        Args:
            model_id: Affected model
            action: Action performed
            from_version: Previous version
            to_version: New version
            actor_id: User who performed action
            actor_ip: IP address of actor
            details: Additional details
            
        Returns:
            Created history record
        """
        history = ModelVersionHistory(
            model_id=model_id,
            action=action,
            from_version=from_version,
            to_version=to_version,
            actor_id=actor_id,
            actor_ip=actor_ip,
            details=details or {}
        )
        
        stmt = select(ModelVersionHistory).filter_by(model_id=history.model_id)
        result = await self.db.execute(stmt)
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        
        return history
    
    async def get_version_history(
        self,
        model_id: UUID,
        limit: int = 50
    ) -> Sequence[ModelVersionHistory]:
        """
        Get version history for a model.
        
        Args:
            model_id: Model UUID
            limit: Maximum number of records
            
        Returns:
            List of history records
        """
        query = select(ModelVersionHistory).where(
            ModelVersionHistory.model_id == model_id
        ).order_by(
            desc(ModelVersionHistory.created_at)
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # ============== Statistics ==============
    
    async def get_model_stats(self) -> Dict[str, Any]:
        """
        Get overall model statistics.
        
        Returns:
            Dictionary with statistics
        """
        # Total models (excluding deleted)
        total_query = select(func.count()).where(
            AIModel.is_deleted == false()
        )
        total_result = await self.db.execute(total_query)
        total_models = total_result.scalar() or 0
        
        # Active models
        active_query = select(func.count()).where(
            AIModel.is_active == True,
            AIModel.is_deleted == false()
        )
        active_result = await self.db.execute(active_query)
        active_models = active_result.scalar() or 0
        
        # Models by type
        type_query = select(
            AIModel.model_type,
            func.count().label('count')
        ).where(
            AIModel.is_deleted == false()
        ).group_by(AIModel.model_type)
        
        type_result = await self.db.execute(type_query)
        models_by_type = {row.model_type: row.count for row in type_result.all()}
        
        return {
            "total_models": total_models,
            "active_models": active_models,
            "models_by_type": models_by_type
        }
