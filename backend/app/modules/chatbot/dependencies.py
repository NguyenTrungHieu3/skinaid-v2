from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies.database import get_db
from app.core.redis import get_redis
from app.modules.chatbot.services.chat_prompt_builder import ChatPromptBuilder
from app.modules.chatbot.services.chat_service import ChatService
from app.modules.llm.services.llm_service import LLMService


def get_llm_service() -> LLMService:
    """Factory cho LLMService — reuse từ llm module."""
    return LLMService()


def get_prompt_builder() -> ChatPromptBuilder:
    """Factory cho ChatPromptBuilder — stateless."""
    return ChatPromptBuilder()


async def get_chat_service(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    llm_service: LLMService = Depends(get_llm_service),
    prompt_builder: ChatPromptBuilder = Depends(get_prompt_builder),
) -> ChatService:
    """Factory cho ChatService — inject tất cả dependencies."""
    return ChatService(
        db=db,
        redis=redis,
        llm_service=llm_service,
        prompt_builder=prompt_builder,
    )


ChatSvcDep = Annotated[ChatService, Depends(get_chat_service)]
