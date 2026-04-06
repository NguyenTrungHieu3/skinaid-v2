from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update, delete, false
from sqlalchemy.orm import selectinload

from app.modules.ai.models.analysis import Analysis
from app.modules.ai.models.detection import Detection
from app.modules.ai.models.ai_results import AIResult
from app.shared.base_repository import BaseRepository
from app.modules.ai.exceptions import WoundAnalysisNotFoundError


class WoundAnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Analysis, db=db)

    async def get_analysis_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        query = select(Analysis).where(
            Analysis.analysis_id == analysis_id
        ).options(
            selectinload(Analysis.wound_detections)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_history(
        self,
        user_id: Optional[UUID] = None,
        guest_session_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Analysis], int]:
        base_query = select(Analysis)

        if user_id:
            base_query = base_query.where(Analysis.user_id == user_id)
        elif guest_session_id:
            base_query = base_query.where(
                Analysis.guest_session_id == guest_session_id)
        else:
            return [], 0

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get items
        query = base_query.options(
            selectinload(Analysis.wound_detections)
        ).order_by(
            desc(Analysis.created_at)
        ).limit(limit).offset(offset)

        result = await self.db.execute(query)
        analyses = result.scalars().all()

        return list(analyses), total

    async def create_analysis(self, analysis_data: Analysis) -> Analysis:
        self.db.add(analysis_data)
        await self.db.flush()
        await self.db.refresh(analysis_data)
        return analysis_data

    async def add_detections(self, detections: List[Detection]) -> None:
        self.db.add_all(detections)
        await self.db.flush()

    async def update_analysis_status(
        self,
        analysis_id: UUID,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        sub_type: Optional[str] = None,
        confidence: Optional[float] = None,
        model_version: Optional[str] = None,
        status_reason: Optional[str] = None,
    ) -> None:
        """Update Analysis status and summary fields after processing completes."""
        values: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
        }
        if started_at is not None:
            values["started_at"] = started_at
        if completed_at is not None:
            values["completed_at"] = completed_at
        if wound_type is not None:
            values["wound_type"] = wound_type
        if severity is not None:
            values["severity"] = severity
        if sub_type is not None:
            values["sub_type"] = sub_type
        if confidence is not None:
            values["confidence"] = confidence
        if model_version is not None:
            values["model_version"] = model_version
        if status_reason is not None:
            values["status_reason"] = status_reason

        stmt = (
            update(Analysis)
            .where(Analysis.analysis_id == analysis_id)
            .values(**values)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def save_ai_result(self, ai_result: AIResult) -> AIResult:
        """Persist a single AIResult record."""
        self.db.add(ai_result)
        await self.db.flush()
        return ai_result

    async def update_detection_snapshot(
        self,
        analysis_id: UUID,
        wound_type: str,
        severity: str,
        snapshot: Dict[str, Any],
    ) -> int:
        """
        Overwrite firstaid_snapshot trên tất cả Detection khớp
        analysis_id + wound_type + severity.
        Trả về số rows đã update.
        """
        stmt = (
            update(Detection)
            .where(
                Detection.analysis_id == analysis_id,
                Detection.wound_type == wound_type,
                Detection.severity == severity,
            )
            .values(firstaid_snapshot=snapshot)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

    async def soft_delete_analysis(self, analysis_id: UUID) -> bool:
        stmt = delete(Analysis).where(
            Analysis.analysis_id == analysis_id
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def get_recent_analyses(self, limit: int = 5) -> List[Analysis]:
        """Get most recent analyses (for admin dashboard etc)."""
        query = select(Analysis).order_by(
            desc(Analysis.created_at)
        ).limit(limit).options(
            selectinload(Analysis.wound_detections)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
