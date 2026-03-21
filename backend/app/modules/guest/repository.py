from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4, UUID

from sqlalchemy import func, select, text, update, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.guest.models.guest_session import GuestSession
from app.modules.ai.models.analysis import Analysis
from app.shared.base_repository import BaseRepository


class GuestRepository(BaseRepository[GuestSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(GuestSession, db)

    async def get_stats(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        total_stmt = select(func.count(GuestSession.session_id))
        total = (await self.db.execute(total_stmt)).scalar() or 0

        active_stmt = select(func.count(GuestSession.session_id)).where(
            GuestSession.is_active == True,
            GuestSession.expires_at >= now
        )
        active = (await self.db.execute(active_stmt)).scalar() or 0

        sum_stmt = select(
            func.coalesce(func.sum(GuestSession.upload_count), 0),
            func.coalesce(func.sum(GuestSession.analysis_count), 0)
        )
        sums = (await self.db.execute(sum_stmt)).one()
        total_uploads = int(sums[0])
        total_analyses = int(sums[1])

        converted_stmt = select(func.count(GuestSession.session_id)).where(
            GuestSession.is_converted_to_user == True
        )
        converted = (await self.db.execute(converted_stmt)).scalar() or 0

        avg_stmt = select(
            func.avg(
                func.extract('epoch', func.coalesce(
                    GuestSession.last_activity_at, now) - GuestSession.created_at)
            )
        )
        avg_seconds = (await self.db.execute(avg_stmt)).scalar() or 0.0
        avg_hours = float(avg_seconds) / 3600.0

        return {
            "total_sessions": total,
            "active_sessions": active,
            "total_uploads": total_uploads,
            "total_analyses": total_analyses,
            "converted_users": converted,
            "average_session_duration": round(avg_hours, 2)
        }

    async def claim_analysis(self, analysis_id: UUID, user_id: UUID) -> bool:
        stmt = (
            update(Analysis)
            .where(
                Analysis.analysis_id == analysis_id,
                Analysis.session_id.is_not(None),
                Analysis.user_id.is_(None)
            )
            .values(
                user_id=user_id,
                session_id=None,
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0
