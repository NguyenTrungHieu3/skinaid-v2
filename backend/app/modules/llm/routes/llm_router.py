from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies.access_control import require_auth
from app.modules.users.models.user import User
from app.modules.llm.dependencies import SynthesisOrchestratorDep
from app.modules.llm.schemas.llm_schemas import (
    LLMSynthesizeRequest,
    LLMSynthesizeResponse,
)
from app.shared.response import SuccessResponse

router = APIRouter(prefix="/llm")


@router.post(
    "/synthesize",
    response_model=SuccessResponse[LLMSynthesizeResponse],
    summary="Tổng hợp hướng dẫn sơ cứu (B5)",
    description=(
        "Nhận kết quả AI (wound_type, severity) và câu trả lời questionnaire của người dùng. "
        "Chạy song song RAG retrieval (Qdrant) và DB lookup (firstaid_guides), "
        "sau đó gọi LLM để tổng hợp hướng dẫn cá nhân hóa. "
        "B6 validation so sánh LLM output với DB guide — nếu không consistent sẽ fallback về DB. "
        "**Yêu cầu xác thực.**"
    ),
)
async def synthesize_response(
    request: LLMSynthesizeRequest,
    orchestrator: SynthesisOrchestratorDep,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    """
    B5 → B6 synthesis pipeline:
    - Parallel: RAG hybrid_search + DB get_guide
    - LLM synthesis (gpt-5-nano)
    - B6 validation: keyword match ≥ 60% → source="llm", else source="db"
    """
    result = await orchestrator.synthesize(request)

    return SuccessResponse(
        message="Tổng hợp hướng dẫn sơ cứu thành công",
        data=result,
    )
