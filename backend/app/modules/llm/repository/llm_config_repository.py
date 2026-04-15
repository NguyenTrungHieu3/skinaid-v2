import logging
from typing import Optional, Sequence
from uuid import UUID

from sqlmodel import select
from sqlalchemy import desc

from app.modules.llm.models.llm_configuration import LLMConfiguration
from app.modules.llm.models.llm_config_change_log import LLMConfigChangeLog
from app.modules.users.models import User
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class LLMConfigRepository(BaseRepository[LLMConfiguration]):
    """Repository for LLM configuration CRUD operations."""

    def __init__(self, db) -> None:
        super().__init__(LLMConfiguration, db)

    async def get_by_config_key(self, config_key: str) -> Optional[LLMConfiguration]:
        """Get a single configuration by its unique key."""
        stmt = select(LLMConfiguration).where(
            LLMConfiguration.config_key == config_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_configs(self) -> Sequence[LLMConfiguration]:
        """Get all LLM configurations ordered by config_key."""
        stmt = select(LLMConfiguration).order_by(LLMConfiguration.config_key)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_config(
        self, config: LLMConfiguration, data: dict
    ) -> LLMConfiguration:
        """Update a configuration with the given data dict."""
        return await self.update(config, data)

    # ── Phase 6: Change logs ─────────────────────────────

    async def get_change_logs(
        self,
        config_key: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Get change logs with config display_name and user email.
        Returns (list_of_dicts, total_count).
        """
        from sqlalchemy import func, select as sa_select

        # Build base query
        base_filter = []
        if config_key:
            base_filter.append(LLMConfiguration.config_key == config_key)

        # Count query
        count_stmt = (
            sa_select(func.count(LLMConfigChangeLog.id))
            .join(LLMConfiguration, LLMConfigChangeLog.config_id == LLMConfiguration.id)
        )
        for f in base_filter:
            count_stmt = count_stmt.where(f)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        # Data query with joins
        stmt = (
            sa_select(
                LLMConfigChangeLog,
                LLMConfiguration.config_key,
                LLMConfiguration.display_name,
                User.email,
            )
            .join(LLMConfiguration, LLMConfigChangeLog.config_id == LLMConfiguration.id)
            .outerjoin(User, LLMConfigChangeLog.changed_by == User.user_id)
        )
        for f in base_filter:
            stmt = stmt.where(f)

        stmt = stmt.order_by(desc(LLMConfigChangeLog.created_at)).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        rows = result.all()

        logs = []
        for row in rows:
            log = row[0]  # LLMConfigChangeLog
            logs.append({
                "id": str(log.id),
                "config_key": row[1],       # config_key
                "display_name": row[2],      # display_name
                "change_type": log.change_type,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "reason": log.reason,
                "changed_by": str(log.changed_by) if log.changed_by else None,
                "changed_by_email": row[3],  # user email
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })

        return logs, total

    # ── Phase 7: Usage stats ─────────────────────────────

    async def get_usage_stats(
        self, period_days: int = 30, config_key: str | None = None
    ) -> list[dict]:
        """
        Aggregate usage statistics per config_key for the given period.
        Optionally filter by config_key.
        """
        from sqlalchemy import func, select as sa_select, case, cast, Float
        from datetime import datetime, timedelta, timezone
        from app.modules.llm.models.llm_usage_stat import LLMUsageStat

        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=period_days)

        stmt = (
            sa_select(
                LLMUsageStat.config_key,
                func.count(LLMUsageStat.id).label("total_requests"),
                func.sum(case((LLMUsageStat.success == True, 1), else_=0)).label("success_count"),
                func.sum(case((LLMUsageStat.success == False, 1), else_=0)).label("error_count"),
                func.coalesce(func.sum(LLMUsageStat.tokens_total), 0).label("total_tokens"),
                func.coalesce(func.sum(LLMUsageStat.tokens_prompt), 0).label("total_prompt_tokens"),
                func.coalesce(func.sum(LLMUsageStat.tokens_completion), 0).label("total_completion_tokens"),
                func.coalesce(
                    func.avg(cast(LLMUsageStat.response_time_ms, Float)), 0
                ).label("avg_response_time_ms"),
                func.max(LLMUsageStat.created_at).label("last_used_at"),
            )
            .where(LLMUsageStat.created_at >= cutoff)
        )

        if config_key:
            stmt = stmt.where(LLMUsageStat.config_key == config_key)

        stmt = stmt.group_by(LLMUsageStat.config_key).order_by(LLMUsageStat.config_key)

        result = await self.db.execute(stmt)
        rows = result.all()

        stats = []
        for row in rows:
            stats.append({
                "config_key": row.config_key,
                "total_requests": row.total_requests,
                "success_count": row.success_count,
                "error_count": row.error_count,
                "total_tokens": row.total_tokens,
                "total_prompt_tokens": row.total_prompt_tokens,
                "total_completion_tokens": row.total_completion_tokens,
                "avg_response_time_ms": round(float(row.avg_response_time_ms), 1),
                "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
            })

        return stats

    # ── Budget settings ───────────────────────────────────

    async def get_budget_settings(self):
        """Get the singleton budget settings row."""
        from app.modules.llm.models.llm_budget_setting import LLMBudgetSetting
        stmt = select(LLMBudgetSetting)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_budget_settings(self, **kwargs):
        """Update budget settings."""
        from app.modules.llm.models.llm_budget_setting import LLMBudgetSetting
        from datetime import datetime, timezone
        stmt = select(LLMBudgetSetting)
        result = await self.db.execute(stmt)
        budget = result.scalar_one_or_none()
        if not budget:
            return None
        for k, v in kwargs.items():
            if hasattr(budget, k):
                setattr(budget, k, v)
        budget.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.commit()
        await self.db.refresh(budget)
        return budget

    # ── Usage totals for current month ────────────────────

    async def get_monthly_usage_totals(self) -> dict:
        """Get token totals for the current calendar month."""
        from sqlalchemy import func, select as sa_select
        from datetime import datetime, timezone
        from app.modules.llm.models.llm_usage_stat import LLMUsageStat

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stmt = sa_select(
            func.coalesce(func.sum(LLMUsageStat.tokens_prompt), 0).label("prompt"),
            func.coalesce(func.sum(LLMUsageStat.tokens_completion), 0).label("completion"),
            func.coalesce(func.sum(LLMUsageStat.tokens_total), 0).label("total"),
        ).where(LLMUsageStat.created_at >= month_start)

        result = await self.db.execute(stmt)
        row = result.one()
        return {
            "prompt_tokens": row.prompt,
            "completion_tokens": row.completion,
            "total_tokens": row.total,
        }


