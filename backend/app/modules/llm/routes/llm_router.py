from fastapi import APIRouter, Depends
from app.modules.llm.services.stub_service import LLMStubService
from app.modules.llm.schemas.llm_schemas import (
    LLMSynthesizeRequest,
    LLMSynthesizeResponse,
)
from app.shared.response import SuccessResponse

router = APIRouter()


@router.post(
    "/synthesize",
    response_model=SuccessResponse[LLMSynthesizeResponse],
    summary="Synthesize LLM response (PBI-25)",
    description="Synthesize a response using LLM based on retrieved knowledge. **Stub:** Returns placeholder until real LLM is implemented.",
)
async def synthesize_response(
    request: LLMSynthesizeRequest,
    stub_service: LLMStubService = Depends(),
) -> SuccessResponse:
    """
    Synthesize a response using LLM based on retrieved knowledge.
    
    **Stub:** Returns placeholder until real LLM is implemented.
    """
    result = await stub_service.synthesize(
        request.query,
        request.context,
        request.max_tokens,
        request.temperature,
        request.system_prompt,
    )
    
    return SuccessResponse(
        message="Tổng hợp phản hồi thành công",
        data=result,
    )
