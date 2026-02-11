from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update, delete
from sqlalchemy.orm import selectinload

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.shared.base_repository import BaseRepository
from app.modules.ai.exceptions import WoundAnalysisNotFoundError


class WoundAnalysisRepository(BaseRepository[WoundAnalysis]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=WoundAnalysis, db=db)

    async def get_analysis_by_id(self, analysis_id: UUID) -> Optional[WoundAnalysis]:
        """
        Get wound analysis by ID with detections loaded.
        """
        query = select(WoundAnalysis).where(
            WoundAnalysis.analysis_id == analysis_id,
            WoundAnalysis.is_deleted == False
        ).options(
            selectinload(WoundAnalysis.wound_detections)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_history(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[WoundAnalysis], int]:
        """
        Get analysis history for user or session.
        Returns (list of analyses, total count).
        """
        base_query = select(WoundAnalysis).where(
            WoundAnalysis.is_deleted == False)

        if user_id:
            base_query = base_query.where(WoundAnalysis.user_id == user_id)
        elif session_id:
            base_query = base_query.where(
                WoundAnalysis.session_id == session_id)
        else:
            # If neither provided, return empty list or all?
            # Logic implies fetching history for specific user/session.
            return [], 0

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get items
        query = base_query.options(
            selectinload(WoundAnalysis.wound_detections)
        ).order_by(
            desc(WoundAnalysis.created_at)
        ).limit(limit).offset(offset)

        result = await self.db.execute(query)
        analyses = result.scalars().all()

        return list(analyses), total

    async def create_analysis(self, analysis_data: WoundAnalysis) -> WoundAnalysis:
        """Create a new analysis record."""
        self.db.add(analysis_data)
        await self.db.flush()
        await self.db.refresh(analysis_data)
        return analysis_data

    async def add_detections(self, detections: List[WoundDetection]) -> None:
        """Add multiple detection records."""
        self.db.add_all(detections)
        await self.db.flush()

    async def soft_delete_analysis(self, analysis_id: UUID) -> bool:
        """Soft delete an analysis record."""
        stmt = update(WoundAnalysis).where(
            WoundAnalysis.analysis_id == analysis_id
        ).values(
            is_deleted=True,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def get_recent_analyses(self, limit: int = 5) -> List[WoundAnalysis]:
        """Get most recent analyses (for admin dashboard etc)."""
        query = select(WoundAnalysis).where(
            WoundAnalysis.is_deleted == False
        ).order_by(
            desc(WoundAnalysis.created_at)
        ).limit(limit).options(
            selectinload(WoundAnalysis.wound_detections)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
