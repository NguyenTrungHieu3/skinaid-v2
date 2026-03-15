from fastapi import APIRouter, Depends, Path
from uuid import UUID
from app.modules.ai.services.model_service import ModelService
from app.modules.ai.schemas.model_schemas import (
    ModelListResponse,
    ModelActivateRequest,
    ModelActivateResponse,
)
from app.shared.response import SuccessResponse

router = APIRouter(tags=["AI Model Management"])


@router.get(
    "/models",
    response_model=SuccessResponse[ModelListResponse],
    summary="List all AI models (PBI-27)",
    description="Get list of all AI models in the system. **Stub:** Returns empty list until real model management is implemented.",
)
async def list_models(
    model_service: ModelService = Depends(),
) -> SuccessResponse:
    """
    Get list of all AI models in the system.

    **Stub:** Returns empty list until real model management is implemented.
    """
    result = await model_service.list_models()

    return SuccessResponse(
        message="Lấy danh sách model thành công",
        data=result,
    )


@router.post(
    "/models/{model_id}/activate",
    response_model=SuccessResponse[ModelActivateResponse],
    summary="Activate an AI model (PBI-27)",
    description="Activate a specific AI model version. **Stub:** Returns success mock response.",
)
async def activate_model(
    model_id: UUID = Path(..., description="Model ID to activate"),
    request: ModelActivateRequest = None,
    model_service: ModelService = Depends(),
) -> SuccessResponse:
    """
    Activate a specific AI model version.

    **Stub:** Returns success mock response.
    """
    result = await model_service.activate_model(model_id)

    return SuccessResponse(
        message="Kích hoạt model thành công",
        data=result,
    )
