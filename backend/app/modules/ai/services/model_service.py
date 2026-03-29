from datetime import datetime
from uuid import UUID, uuid4
from typing import List
import logging

from app.modules.ai.schemas.model_schemas import (
    ModelListResponse,
    ModelActivateResponse,
    ModelInfo,
)

logger = logging.getLogger(__name__)


class ModelService:
    """
    Service for managing AI models (PBI-27).

    Returns mock responses until real model management is implemented.
    """

    def __init__(self):
        self.active_version = None

    async def list_models(self) -> ModelListResponse:
        """
        Return stub model list.

        Returns:
            ModelListResponse with empty models list
        """
        logger.info("[AI MODEL STUB] Listing models")

        # Return empty list for now
        return ModelListResponse(
            models=[],
            active_version=self.active_version,
            total=0,
        )

    async def activate_model(self, model_id: UUID) -> ModelActivateResponse:
        """
        Return stub model activation response.

        Args:
            model_id: UUID of model to activate

        Returns:
            ModelActivateResponse with mock success
        """
        logger.info(f"[AI MODEL STUB] Activating model: {model_id}")

        previous_version = self.active_version
        self.active_version = "v1.0"

        return ModelActivateResponse(
            success=True,
            active_version=self.active_version,
            previous_version=previous_version,
        )
