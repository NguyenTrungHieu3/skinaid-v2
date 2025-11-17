from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID
from datetime import datetime, timedelta

from app.modules.guest.models.guest_session import GuestSession
from app.modules.ai.models.wound_analysis import WoundAnalysis

class GuestSessionService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self,
        ip_address: str,
        user_agent: str
    ) -> GuestSession:
        session = GuestSession(
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_session(self, session_id: UUID) -> GuestSession:
        return await self.db.get(GuestSession, session_id)
    
    async def validate_session(self, session_id: UUID) -> bool:
        session = await self.get_session(session_id)
        
        if not session:
            return False
        
        return (
            session.is_active and
            session.expires_at > datetime.now() and
            not session.is_converted_to_user
        )
    
    async def get_session_analyses(
        self,
        session_id: UUID,
        limit: int = 50
    ) -> list[WoundAnalysis]:
        statement = select(WoundAnalysis).where(
            WoundAnalysis.session_id == session_id,
            WoundAnalysis.is_deleted == False
        ).order_by(WoundAnalysis.analyzed_at.desc()).limit(limit)
        
        result = await self.db.execute(statement)
        return result.scalars().all()