from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies.database import get_db
from app.modules.llm.services.llm_service import LLMService
from app.modules.llm.services.prompt_builder import PromptBuilder
from app.modules.llm.services.synthesis_orchestrator import SynthesisOrchestrator


def get_llm_service() -> LLMService:
    """Factory cho LLMService — tạo mới mỗi request (stateless ngoại trừ lazy-init client)."""
    return LLMService()


def get_prompt_builder() -> PromptBuilder:
    """Factory cho PromptBuilder — stateless."""
    return PromptBuilder()


async def get_synthesis_orchestrator(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
) -> SynthesisOrchestrator:
    """Factory cho SynthesisOrchestrator — inject db session cho FirstAidService bên trong."""
    return SynthesisOrchestrator(
        db=db,
        llm_service=llm_service,
        prompt_builder=prompt_builder,
    )


# Annotated shorthand cho dùng trong route function signature
LLMSvc = Annotated[LLMService, Depends(get_llm_service)]
SynthesisOrchestratorDep = Annotated[SynthesisOrchestrator, Depends(get_synthesis_orchestrator)]
