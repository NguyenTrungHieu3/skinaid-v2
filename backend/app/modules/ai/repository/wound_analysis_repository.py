from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update, delete, false
from sqlalchemy.orm import selectinload

from app.modules.ai.models.analysis import Analysis
from app.modules.ai.models.detection import Detection
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

    async def soft_delete_analysis(self, analysis_id: UUID) -> bool:
        stmt = delete(Analysis).where(
            Analysis.analysis_id == analysis_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
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
