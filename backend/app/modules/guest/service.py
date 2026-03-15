import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.guest.models.guest_session import GuestSession
from app.modules.guest.repository import GuestRepository
from app.modules.guest.exceptions import GuestSessionNotFoundError, AnalysisClaimError
from app.modules.guest.schemas.api import CreateGuestSessionRequest, GuestStatsResponse

logger = logging.getLogger(__name__)


class GuestService:
    def __init__(self, repository: GuestRepository, db: AsyncSession):
        self.repository = repository
        self.db = db

    async def create_session(
        self, request: CreateGuestSessionRequest
    ) -> GuestSession:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = now + timedelta(hours=1)

        session = GuestSession(
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            created_at=now,
            expires_at=expires_at,
            last_activity_at=now,
            is_active=True
        )

        created = await self.repository.create(session)
        await self.db.flush()
        await self.db.refresh(created)
        return created

    async def get_session(self, session_id: uuid.UUID) -> GuestSession:
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise GuestSessionNotFoundError(str(session_id))

        return session

    async def get_stats(self) -> GuestStatsResponse:
        stats = await self.repository.get_stats()
        return GuestStatsResponse(**stats)

    async def claim_analysis(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        success = await self.repository.claim_analysis(analysis_id, user_id)
        if not success:
            raise AnalysisClaimError("Analysis not found or already claimed")
        return True
