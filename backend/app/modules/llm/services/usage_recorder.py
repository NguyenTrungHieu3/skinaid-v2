"""Fire-and-forget usage stats recorder for LLM calls."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def record_llm_usage(
    config_key: str,
    model_name: str,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    tokens_total: int = 0,
    response_time_ms: int = 0,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """
    Record a single LLM usage entry to the database.
    Uses its own session (fire-and-forget) so callers are not blocked.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.modules.llm.models.llm_usage_stat import LLMUsageStat

        async with AsyncSessionLocal() as session:
            stat = LLMUsageStat(
                config_key=config_key,
                model_name=model_name,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
                tokens_total=tokens_total,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message[:500] if error_message else None,
            )
            session.add(stat)
            await session.commit()
    except Exception as exc:
        # Never let usage recording break the main flow
        logger.warning("[UsageRecorder] Failed to record usage: %s", str(exc)[:200])


def fire_and_forget_usage(
    config_key: str,
    model_name: str,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    tokens_total: int = 0,
    response_time_ms: int = 0,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """
    Schedule usage recording as a background task.
    Safe to call from sync or async context — will not block.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(record_llm_usage(
            config_key=config_key,
            model_name=model_name,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tokens_total=tokens_total,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
        ))
    except RuntimeError:
        # No running loop — skip silently
        logger.debug("[UsageRecorder] No event loop, skipping usage recording.")
