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
        """Tạo phiên khách mới."""
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
        # BaseRepository creates but might not commit if we don't tell it?
        # create() usually does add+flush.
        # We need to commit.
        await self.db.commit()
        await self.db.refresh(created)
        return created

    async def get_session(self, session_id: uuid.UUID) -> GuestSession:
        """Lấy thông tin phiên khách."""
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise GuestSessionNotFoundError(str(session_id))

        # Check expiry logic?
        # If expired, do we update status?
        # Old service just returned computed properties.
        # But maybe we should update last_activity?
        # Usually GET doesn't update, but for guest session keeping it alive?
        # "last_activity_at" implies activity. Reading session is activity?
        # If so, update it.
        # But old service "get_guest_session" only selected.
        return session

    async def get_stats(self) -> GuestStatsResponse:
        stats = await self.repository.get_stats()
        return GuestStatsResponse(**stats)

    async def claim_analysis(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Guest chuyển analysis cho User."""
        # Note: logic check ownership or session validity usually happens before.
        # Here we just execute the claim.
        success = await self.repository.claim_analysis(analysis_id, user_id)
        if success:
            await self.db.commit()
            return True
        return False
        # If failure, maybe raise?
        # "False" indicates analysis not found or already claimed.
        # I'll raise exception if False to be explicit?
        # Or return bool.
        # Implementation plan: "raise module-specific exceptions".
        if not success:
            raise AnalysisClaimError("Analysis not found or already claimed")
        return True
