from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, status

from app.shared.response import SuccessResponse
from app.modules.questionnaires.dependencies_user import UserQuestionnaireSvc
from app.modules.questionnaires.schemas.user_api import (
    ResolveQuestionnairesRequest,
    ResolveQuestionnairesResponse,
    SubmitWoundResponseRequest,
    SubmitWoundResponseResponse,
    SynthesisSummary,
)
from app.modules.llm.dependencies import SynthesisOrchestratorDep
from app.modules.llm.schemas.llm_schemas import LLMSynthesizeRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wound-responses")


@router.post(
    "/resolve-questionnaires",
    response_model=SuccessResponse[ResolveQuestionnairesResponse],
    status_code=status.HTTP_200_OK,
    summary="Giải bộ câu hỏi từ danh sách vết thương AI phát hiện",
    description=(
        "Dedupe detections theo (wound_type, subtype). Với mỗi key duy nhất, "
        "chọn severity cao nhất rồi lookup bộ câu hỏi active. "
        "Cùng wound_type+subtype khác severity → 1 bộ; khác wound_type hoặc "
        "khác subtype → bộ riêng."
    ),
)
async def resolve_questionnaires(
    payload: ResolveQuestionnairesRequest,
    service: UserQuestionnaireSvc,
):
    data = await service.resolve_questionnaires(payload.detections)
    return SuccessResponse(data=data)


@router.post(
    "/submit",
    response_model=SuccessResponse[SubmitWoundResponseResponse],
    status_code=status.HTTP_200_OK,
    summary="Gửi câu trả lời user và (tuỳ chọn) forward sang B5 synthesis",
    description=(
        "Validate (question_id, answer_id) thuộc bộ câu hỏi active, tổng hợp "
        "triage (max red>yellow>green), gọi LLM synthesize per (wound_type, "
        "subtype, severity) nếu forward_to_synthesis=True."
    ),
)
async def submit_response(
    payload: SubmitWoundResponseRequest,
    service: UserQuestionnaireSvc,
    orchestrator: SynthesisOrchestratorDep,
):
    async def _synthesize(
        wound_type: str,
        subtype: Optional[str],
        severity: str,
        user_description: str,
    ) -> Optional[SynthesisSummary]:
        request = LLMSynthesizeRequest(
            wound_type=wound_type,
            severity=severity,
            sub_type=subtype,
            user_description=user_description or "",
        )
        result = await orchestrator.synthesize(request)
        return SynthesisSummary(
            wound_type=wound_type,
            subtype=subtype,
            severity=severity,
            source=result.source,
            guidance=result.guidance,
            structured_guidance=(
                result.structured_guidance.model_dump()
                if result.structured_guidance is not None
                else None
            ),
            validated=result.validated,
        )

    data = await service.submit(payload, synthesize_fn=_synthesize)
    return SuccessResponse(data=data)
