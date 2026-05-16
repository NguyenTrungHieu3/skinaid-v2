"""
Resolve LLM config from database for a given config_key.
Returns model_name, temperature, max_tokens, top_k + validates active/maintenance.
Falls back to .env if config not found in DB.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.modules.llm.models.llm_configuration import LLMConfiguration
from app.modules.llm.exceptions import LLMMaintenanceError, LLMInactiveError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedConfig:
    """Immutable resolved config ready for LLM call."""
    config_key: str
    model_name: str
    temperature: float
    max_tokens: int
    top_k: int


# ── .env fallback defaults ───────────────────────────────────────────
_ENV_DEFAULTS = {
    "synthesis": lambda: ResolvedConfig(
        config_key="synthesis",
        model_name=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        top_k=getattr(settings, "LLM_TOP_K", 5),
    ),
    "chatbot_advisor": lambda: ResolvedConfig(
        config_key="chatbot_advisor",
        model_name=getattr(settings, "CHATBOT_ADVISOR_MODEL", settings.LLM_MODEL),
        temperature=getattr(settings, "CHATBOT_ADVISOR_TEMPERATURE", 0.3),
        max_tokens=getattr(settings, "CHATBOT_ADVISOR_MAX_TOKENS", 1000),
        top_k=getattr(settings, "CHATBOT_ADVISOR_TOP_K", 3),
    ),
    "chatbot_guide": lambda: ResolvedConfig(
        config_key="chatbot_guide",
        model_name=getattr(settings, "CHATBOT_GUIDE_MODEL", settings.LLM_MODEL),
        temperature=getattr(settings, "CHATBOT_GUIDE_TEMPERATURE", 0.7),
        max_tokens=getattr(settings, "CHATBOT_GUIDE_MAX_TOKENS", 500),
        top_k=getattr(settings, "CHATBOT_GUIDE_TOP_K", 3),
    ),
}


async def resolve_llm_config(
    db: AsyncSession,
    config_key: str,
    *,
    check_active: bool = True,
    check_maintenance: bool = True,
) -> ResolvedConfig:
    """
    Resolve LLM config from DB, with .env fallback.

    Args:
        db: Active database session
        config_key: One of 'synthesis', 'chatbot_advisor', 'chatbot_guide'
        check_active: If True, raise LLMInactiveError when is_active=False
        check_maintenance: If True, raise LLMMaintenanceError when is_maintenance=True

    Returns:
        ResolvedConfig with model_name, temperature, max_tokens, top_k

    Raises:
        LLMInactiveError: Config is not active
        LLMMaintenanceError: Config is in maintenance mode
    """
    # Try DB first
    try:
        stmt = select(LLMConfiguration).where(
            LLMConfiguration.config_key == config_key
        )
        result = await db.execute(stmt)
        cfg: Optional[LLMConfiguration] = result.scalar_one_or_none()
    except Exception as exc:
        logger.warning(
            "[ConfigResolver] DB query failed for '%s', using .env fallback: %s",
            config_key, str(exc)[:100],
        )
        try:
            await db.rollback()
        except Exception as rollback_exc:
            logger.warning(
                "[ConfigResolver] DB rollback failed after config query error: %s",
                str(rollback_exc)[:100],
            )
        cfg = None

    if cfg is None:
        # Fallback to .env
        fallback_fn = _ENV_DEFAULTS.get(config_key)
        if fallback_fn:
            logger.info(
                "[ConfigResolver] Config '%s' not in DB, using .env fallback.",
                config_key,
            )
            return fallback_fn()
        # Unknown config_key — use global .env defaults
        return ResolvedConfig(
            config_key=config_key,
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_k=getattr(settings, "LLM_TOP_K", 5),
        )

    # Check active status
    if check_active and not cfg.is_active:
        logger.warning("[ConfigResolver] Config '%s' is INACTIVE.", config_key)
        raise LLMInactiveError(
            message=f"Chức năng '{cfg.display_name}' hiện đang tắt",
            details={"config_key": config_key},
        )

    # Check maintenance
    if check_maintenance and cfg.is_maintenance:
        msg = cfg.maintenance_message or "Đang trong chế độ bảo trì, vui lòng thử lại sau"
        logger.warning("[ConfigResolver] Config '%s' is in MAINTENANCE.", config_key)
        raise LLMMaintenanceError(
            message=msg,
            details={"config_key": config_key},
        )

    logger.debug(
        "[ConfigResolver] Resolved '%s': model=%s, temp=%.2f, max_tokens=%d",
        config_key, cfg.model_name, cfg.temperature, cfg.max_tokens,
    )

    return ResolvedConfig(
        config_key=config_key,
        model_name=cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        top_k=cfg.top_k,
    )
