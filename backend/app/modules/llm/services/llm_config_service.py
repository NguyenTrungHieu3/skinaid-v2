from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.llm.models.llm_configuration import LLMConfiguration
from app.modules.llm.models.llm_config_change_log import LLMConfigChangeLog
from app.modules.llm.repository.llm_config_repository import LLMConfigRepository

logger = logging.getLogger(__name__)

# .env default values — used when no DB row exists
_ENV_DEFAULTS = {
    "synthesis": {
        "model_name": settings.LLM_MODEL,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "top_k": settings.LLM_SYNTHESIS_TOP_K,
    },
    "chatbot_advisor": {
        "model_name": settings.LLM_MODEL,
        "temperature": settings.CHATBOT_ADVISOR_TEMPERATURE,
        "max_tokens": settings.CHATBOT_ADVISOR_MAX_TOKENS,
        "top_k": 3,
    },
    "chatbot_guide": {
        "model_name": settings.LLM_MODEL,
        "temperature": settings.CHATBOT_GUIDE_TEMPERATURE,
        "max_tokens": settings.CHATBOT_GUIDE_MAX_TOKENS,
        "top_k": 3,
    },
}

# Available models for admin selection
AVAILABLE_MODELS = [
    {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "description": "Cân bằng chất lượng/chi phí", "tier": "mid"},
    {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano", "description": "Nhanh, rẻ, phù hợp chatbot", "tier": "low"},
    {"id": "gpt-4.1", "name": "GPT-4.1", "description": "Chất lượng cao nhất", "tier": "high"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Legacy model, nhẹ", "tier": "low"},
    {"id": "gpt-4o", "name": "GPT-4o", "description": "Legacy model, mạnh", "tier": "high"},
]

_VALID_MODEL_IDS = {m["id"] for m in AVAILABLE_MODELS}


class LLMConfigService:
    """Service layer for LLM configuration management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = LLMConfigRepository(db)

    # ── Private helpers ──────────────────────────────────────

    def _serialize_config(self, cfg: LLMConfiguration) -> Dict[str, Any]:
        """Convert a LLMConfiguration ORM object into a dict for API response."""
        env_defaults = _ENV_DEFAULTS.get(cfg.config_key, {})
        return {
            "id": str(cfg.id),
            "config_key": cfg.config_key,
            "display_name": cfg.display_name,
            "description": cfg.description,
            "model_name": cfg.model_name,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "top_k": cfg.top_k,
            "is_active": cfg.is_active,
            "is_maintenance": cfg.is_maintenance,
            "maintenance_message": cfg.maintenance_message,
            "env_defaults": env_defaults,
            "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
            "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
        }

    async def _log_change(
        self,
        config: LLMConfiguration,
        change_type: str,
        old_values: Dict[str, Any] | None,
        new_values: Dict[str, Any] | None,
        changed_by: UUID | None = None,
        reason: str | None = None,
    ) -> None:
        """Write a change log entry for audit trail."""
        log_entry = LLMConfigChangeLog(
            config_id=config.id,
            changed_by=changed_by,
            change_type=change_type,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
        )
        self._db.add(log_entry)
        await self._db.flush()
        logger.info(
            "[LLMConfigService] Change logged: type=%s, config=%s, by=%s",
            change_type, config.config_key, changed_by,
        )

    # ── Phase 1: Read operations ─────────────────────────────

    async def get_all_configs(self) -> List[Dict[str, Any]]:
        """Get all LLM configurations with .env fallback info."""
        configs = await self._repo.get_all_configs()
        return [self._serialize_config(cfg) for cfg in configs]

    async def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """Get a single config by key with env defaults."""
        cfg = await self._repo.get_by_config_key(config_key)
        if not cfg:
            return None
        return self._serialize_config(cfg)

    async def get_effective_config(self, config_key: str) -> Dict[str, Any]:
        """
        Get the effective config for runtime use.
        DB values override .env defaults.
        Returns model_name, temperature, max_tokens, top_k, is_active, is_maintenance.
        """
        cfg = await self._repo.get_by_config_key(config_key)
        env = _ENV_DEFAULTS.get(config_key, {})

        if cfg:
            return {
                "model_name": cfg.model_name,
                "temperature": cfg.temperature,
                "max_tokens": cfg.max_tokens,
                "top_k": cfg.top_k,
                "is_active": cfg.is_active,
                "is_maintenance": cfg.is_maintenance,
                "maintenance_message": cfg.maintenance_message,
            }
        else:
            # Fallback to .env defaults
            return {
                "model_name": env.get("model_name", settings.LLM_MODEL),
                "temperature": env.get("temperature", 0.3),
                "max_tokens": env.get("max_tokens", 2000),
                "top_k": env.get("top_k", 5),
                "is_active": True,
                "is_maintenance": False,
                "maintenance_message": None,
            }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Return list of available LLM models for admin selection."""
        return AVAILABLE_MODELS

    # ── Phase 2: Switch model & Maintenance ────────────────

    async def switch_model(
        self,
        config_key: str,
        new_model: str,
        admin_id: UUID | None = None,
        reason: str | None = None,
    ) -> Dict[str, Any]:
        """
        Switch LLM model for a config.
        Flow: enable maintenance → change model → disable maintenance.
        Returns the result dict.
        """
        cfg = await self._repo.get_by_config_key(config_key)
        if not cfg:
            raise ValueError(f"Config '{config_key}' không tồn tại")

        if new_model not in _VALID_MODEL_IDS:
            raise ValueError(
                f"Model '{new_model}' không hợp lệ. "
                f"Các model khả dụng: {', '.join(sorted(_VALID_MODEL_IDS))}"
            )

        old_model = cfg.model_name
        if old_model == new_model:
            raise ValueError(f"Config '{config_key}' đã đang dùng model '{new_model}'")

        # Step 1: Enable maintenance mode
        await self._repo.update_config(cfg, {
            "is_maintenance": True,
            "maintenance_message": f"Đang chuyển model từ {old_model} sang {new_model}...",
            "updated_by": admin_id,
        })
        await self._db.flush()

        # Step 2: Switch model
        await self._repo.update_config(cfg, {
            "model_name": new_model,
        })
        await self._db.flush()

        # Step 3: Disable maintenance mode
        await self._repo.update_config(cfg, {
            "is_maintenance": False,
            "maintenance_message": None,
        })

        # Log the change
        await self._log_change(
            config=cfg,
            change_type="model_change",
            old_values={"model_name": old_model},
            new_values={"model_name": new_model},
            changed_by=admin_id,
            reason=reason,
        )

        await self._db.commit()

        logger.info(
            "[LLMConfigService] Model switched: %s → %s for config '%s'",
            old_model, new_model, config_key,
        )

        return {
            "config_key": config_key,
            "old_model": old_model,
            "new_model": new_model,
            "is_maintenance": False,
            "message": f"Đã chuyển model từ {old_model} sang {new_model} thành công",
        }

    async def set_maintenance(
        self,
        config_key: str,
        enabled: bool,
        message: str | None = None,
        admin_id: UUID | None = None,
    ) -> Dict[str, Any]:
        """Toggle maintenance mode for a config."""
        cfg = await self._repo.get_by_config_key(config_key)
        if not cfg:
            raise ValueError(f"Config '{config_key}' không tồn tại")

        old_maintenance = cfg.is_maintenance

        await self._repo.update_config(cfg, {
            "is_maintenance": enabled,
            "maintenance_message": message if enabled else None,
            "updated_by": admin_id,
        })

        # Log the change
        change_type = "maintenance_on" if enabled else "maintenance_off"
        await self._log_change(
            config=cfg,
            change_type=change_type,
            old_values={"is_maintenance": old_maintenance},
            new_values={"is_maintenance": enabled, "maintenance_message": message},
            changed_by=admin_id,
        )

        await self._db.commit()

        status_text = "bật" if enabled else "tắt"
        logger.info(
            "[LLMConfigService] Maintenance %s for config '%s'",
            status_text, config_key,
        )

        return self._serialize_config(cfg)

    # ── Phase 3: Activate / Deactivate ─────────────────────

    async def toggle_active(
        self,
        config_key: str,
        is_active: bool,
        admin_id: UUID | None = None,
        reason: str | None = None,
    ) -> Dict[str, Any]:
        """
        Activate or deactivate LLM for a config.
        When deactivated, the system should fallback to DB guide (no LLM calls).
        """
        cfg = await self._repo.get_by_config_key(config_key)
        if not cfg:
            raise ValueError(f"Config '{config_key}' không tồn tại")

        old_active = cfg.is_active
        if old_active == is_active:
            status = "kích hoạt" if is_active else "tắt"
            raise ValueError(f"Config '{config_key}' đã đang ở trạng thái {status}")

        await self._repo.update_config(cfg, {
            "is_active": is_active,
            "updated_by": admin_id,
        })

        # Log the change
        change_type = "activate" if is_active else "deactivate"
        await self._log_change(
            config=cfg,
            change_type=change_type,
            old_values={"is_active": old_active},
            new_values={"is_active": is_active},
            changed_by=admin_id,
            reason=reason,
        )

        await self._db.commit()

        status_text = "kích hoạt" if is_active else "tắt"
        logger.info(
            "[LLMConfigService] Config '%s' %s by admin %s",
            config_key, status_text, admin_id,
        )

        return self._serialize_config(cfg)

    # ── Phase 4: Update Parameters ─────────────────────────

    async def update_params(
        self,
        config_key: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_k: int | None = None,
        admin_id: UUID | None = None,
        reason: str | None = None,
    ) -> Dict[str, Any]:
        """
        Update LLM parameters (temperature, max_tokens, top_k).
        Only provided (non-None) fields are updated.
        """
        cfg = await self._repo.get_by_config_key(config_key)
        if not cfg:
            raise ValueError(f"Config '{config_key}' không tồn tại")

        # Build update dict + track old values
        update_data: Dict[str, Any] = {"updated_by": admin_id}
        old_values: Dict[str, Any] = {}
        new_values: Dict[str, Any] = {}

        if temperature is not None:
            old_values["temperature"] = cfg.temperature
            new_values["temperature"] = temperature
            update_data["temperature"] = temperature

        if max_tokens is not None:
            old_values["max_tokens"] = cfg.max_tokens
            new_values["max_tokens"] = max_tokens
            update_data["max_tokens"] = max_tokens

        if top_k is not None:
            old_values["top_k"] = cfg.top_k
            new_values["top_k"] = top_k
            update_data["top_k"] = top_k

        if not new_values:
            raise ValueError("Không có tham số nào được thay đổi")

        await self._repo.update_config(cfg, update_data)

        # Log the change
        await self._log_change(
            config=cfg,
            change_type="param_update",
            old_values=old_values,
            new_values=new_values,
            changed_by=admin_id,
            reason=reason,
        )

        await self._db.commit()

        logger.info(
            "[LLMConfigService] Params updated for '%s': %s → %s",
            config_key, old_values, new_values,
        )

        return self._serialize_config(cfg)

    # ── Phase 5: Test Prompt ───────────────────────────────

    async def test_prompt(
        self,
        config_key: str,
        prompt: str,
        model_override: str | None = None,
    ) -> Dict[str, Any]:
        """
        Send a test prompt to the LLM and return the response.
        Uses the config's current model/params unless model_override is set.
        """
        import time
        from openai import AsyncOpenAI
        from app.modules.llm.services.llm_config_service import AVAILABLE_MODELS, _VALID_MODEL_IDS

        cfg = await self._repo.get_by_config_key(config_key)
        if not cfg:
            raise ValueError(f"Config '{config_key}' không tồn tại")

        # Determine model to use
        model_to_use = model_override or cfg.model_name
        if model_override and model_override not in _VALID_MODEL_IDS:
            raise ValueError(
                f"Model '{model_override}' không hợp lệ. "
                f"Các model khả dụng: {', '.join(sorted(_VALID_MODEL_IDS))}"
            )

        # Build messages
        messages = [
            {"role": "system", "content": "Bạn là trợ lý AI hữu ích. Trả lời ngắn gọn và chính xác."},
            {"role": "user", "content": prompt},
        ]

        # Call OpenAI directly (not through LLMService to allow model override)
        client = AsyncOpenAI(
            api_key=settings.OPEN_API_KEY,
            max_retries=0,
            timeout=30.0,
        )

        start_ms = time.monotonic()

        try:
            response = await client.chat.completions.create(
                model=model_to_use,
                messages=messages,  # type: ignore[arg-type]
                max_completion_tokens=min(cfg.max_tokens, 1000),  # Cap test at 1000 tokens
                temperature=cfg.temperature,
            )
        except Exception as exc:
            # Record failed test
            from app.modules.llm.services.usage_recorder import fire_and_forget_usage
            _elapsed = int((time.monotonic() - start_ms) * 1000)
            fire_and_forget_usage(
                config_key=config_key,
                model_name=model_to_use,
                response_time_ms=_elapsed,
                success=False,
                error_message=str(exc)[:200],
            )
            raise ValueError(f"Lỗi khi gọi LLM: {str(exc)[:300]}")

        elapsed_ms = int((time.monotonic() - start_ms) * 1000)

        choice = response.choices[0] if response.choices else None
        content = (
            choice.message.content.strip()
            if choice and choice.message.content
            else "(Không có phản hồi)"
        )
        tokens_used = response.usage.total_tokens if response.usage else 0
        _prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        _completion_tokens = response.usage.completion_tokens if response.usage else 0

        # Record successful test
        from app.modules.llm.services.usage_recorder import fire_and_forget_usage
        fire_and_forget_usage(
            config_key=config_key,
            model_name=model_to_use,
            tokens_prompt=_prompt_tokens,
            tokens_completion=_completion_tokens,
            tokens_total=tokens_used,
            response_time_ms=elapsed_ms,
            success=True,
        )

        logger.info(
            "[LLMConfigService] Test prompt for '%s': model=%s, tokens=%d, time=%dms",
            config_key, model_to_use, tokens_used, elapsed_ms,
        )

        return {
            "config_key": config_key,
            "model_used": model_to_use,
            "prompt": prompt,
            "response": content,
            "tokens_used": tokens_used,
            "response_time_ms": elapsed_ms,
        }

    # ── Phase 6: Change Logs ───────────────────────────────

    async def get_change_logs(
        self,
        config_key: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get audit log entries with pagination."""
        logs, total = await self._repo.get_change_logs(
            config_key=config_key,
            limit=limit,
            offset=offset,
        )
        return {"logs": logs, "total": total}

    # ── Phase 7: Usage Statistics ──────────────────────────

    async def get_usage_stats(
        self, period_days: int = 30, config_key: str | None = None
    ) -> Dict[str, Any]:
        """Get aggregated usage statistics with cost estimation."""
        # Get per-config stats from repo (with optional filter)
        raw_stats = await self._repo.get_usage_stats(
            period_days=period_days, config_key=config_key
        )

        # Get config display names
        all_configs = await self._repo.get_all_configs()
        display_map = {c.config_key: c.display_name for c in all_configs}

        # Get budget settings for cost calculation
        budget_settings = await self._repo.get_budget_settings()

        # Build per-config with display_name
        per_config = []
        total_requests = 0
        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_success = 0
        weighted_time = 0.0

        for s in raw_stats:
            s["display_name"] = display_map.get(s["config_key"], s["config_key"])
            per_config.append(s)
            total_requests += s["total_requests"]
            total_tokens += s["total_tokens"]
            total_prompt_tokens += s.get("total_prompt_tokens", 0)
            total_completion_tokens += s.get("total_completion_tokens", 0)
            total_success += s["success_count"]
            weighted_time += s["avg_response_time_ms"] * s["total_requests"]

        avg_time = round(weighted_time / total_requests, 1) if total_requests > 0 else 0
        success_rate = round((total_success / total_requests) * 100, 1) if total_requests > 0 else 100.0

        # Cost estimation
        estimated_cost = 0.0
        budget_info = None
        if budget_settings:
            input_price = budget_settings.price_per_1k_input_tokens
            output_price = budget_settings.price_per_1k_output_tokens
            estimated_cost = round(
                (total_prompt_tokens / 1000 * input_price)
                + (total_completion_tokens / 1000 * output_price),
                6,
            )

            # Monthly budget info
            monthly = await self._repo.get_monthly_usage_totals()
            monthly_cost = round(
                (monthly["prompt_tokens"] / 1000 * input_price)
                + (monthly["completion_tokens"] / 1000 * output_price),
                6,
            )
            budget_pct = 0.0
            if budget_settings.monthly_budget_usd > 0:
                budget_pct = round(
                    (monthly_cost / budget_settings.monthly_budget_usd) * 100, 1
                )

            budget_info = {
                "monthly_budget_usd": budget_settings.monthly_budget_usd,
                "price_per_1k_input_tokens": input_price,
                "price_per_1k_output_tokens": output_price,
                "currency": budget_settings.currency,
                "monthly_prompt_tokens": monthly["prompt_tokens"],
                "monthly_completion_tokens": monthly["completion_tokens"],
                "monthly_total_tokens": monthly["total_tokens"],
                "monthly_estimated_cost": monthly_cost,
                "budget_usage_percent": budget_pct,
            }

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "estimated_cost": estimated_cost,
            "avg_response_time_ms": avg_time,
            "success_rate": success_rate,
            "per_config": per_config,
            "period_days": period_days,
            "budget": budget_info,
        }

    # ── Budget settings ───────────────────────────────────

    async def get_budget_settings(self) -> Dict[str, Any]:
        """Get budget and pricing settings."""
        budget = await self._repo.get_budget_settings()
        if not budget:
            return {
                "monthly_budget_usd": 0,
                "price_per_1k_input_tokens": 0.40,
                "price_per_1k_output_tokens": 1.60,
                "currency": "USD",
                "updated_at": None,
            }
        return {
            "monthly_budget_usd": budget.monthly_budget_usd,
            "price_per_1k_input_tokens": budget.price_per_1k_input_tokens,
            "price_per_1k_output_tokens": budget.price_per_1k_output_tokens,
            "currency": budget.currency,
            "updated_at": budget.updated_at.isoformat() if budget.updated_at else None,
        }

    async def update_budget_settings(
        self, user_id, **kwargs
    ) -> Dict[str, Any]:
        """Update budget and pricing settings."""
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            raise ValueError("Không có giá trị nào để cập nhật")

        updates["updated_by"] = user_id
        budget = await self._repo.update_budget_settings(**updates)
        if not budget:
            raise ValueError("Chưa có cài đặt budget")

        return {
            "monthly_budget_usd": budget.monthly_budget_usd,
            "price_per_1k_input_tokens": budget.price_per_1k_input_tokens,
            "price_per_1k_output_tokens": budget.price_per_1k_output_tokens,
            "currency": budget.currency,
            "updated_at": budget.updated_at.isoformat() if budget.updated_at else None,
        }
