from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ai.models.analysis import Analysis


class WoundContextLoader:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def load_analysis(self, analysis_id: UUID, user_id: UUID) -> Analysis | None:
        stmt = (
            select(Analysis)
            .options(selectinload(Analysis.wound_detections))
            .where(Analysis.analysis_id == analysis_id)
        )
        result = await self._db.execute(stmt)
        analysis = result.scalar_one_or_none()

        if not analysis:
            return None
        if analysis.user_id != user_id:
            return None
        if analysis.status != "completed":
            return None
        return analysis

    async def load_wound_context(
        self,
        analysis_id: UUID | None,
    ) -> tuple[str, str, str | None, dict[str, Any] | None]:
        if not analysis_id:
            return "unknown", "unknown", None, None

        stmt = (
            select(Analysis)
            .options(selectinload(Analysis.wound_detections))
            .where(Analysis.analysis_id == analysis_id)
        )
        result = await self._db.execute(stmt)
        analysis = result.scalar_one_or_none()

        if not analysis or not analysis.wound_detections:
            return "unknown", "unknown", None, None

        det = max(analysis.wound_detections, key=lambda d: d.confidence or 0)
        return (
            det.wound_type or "unknown",
            det.severity or "unknown",
            det.sub_type,
            det.firstaid_snapshot,
        )
