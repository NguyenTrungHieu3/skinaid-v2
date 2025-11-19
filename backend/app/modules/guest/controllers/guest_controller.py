from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.modules.guest.services.guest_service import GuestService
from app.shared.schemas.response import SuccessResponse
from fastapi import HTTPException

class GuestController:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.guest_service = GuestService(db)
    
    async def create_guest_session(
        self, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SuccessResponse:
        """
        Tạo guest session mới.
        
        Returns:
            SuccessResponse với session data bao gồm session_id
        """
        session = await self.guest_service.create_guest_session(
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return SuccessResponse(
            message="Tạo guest session thành công",
            data=session
        )
    
    async def get_guest_session(
        self, 
        session_id: uuid.UUID
    ) -> SuccessResponse:
        """
        Lấy thông tin guest session.
        
        Args:
            session_id: UUID của session
            
        Returns:
            SuccessResponse với thông tin session
            
        Raises:
            HTTPException 404: Nếu session không tồn tại
        """
        session = await self.guest_service.get_guest_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session không tồn tại")
        
        return SuccessResponse(
            message="Lấy session thành công",
            data=session
        )
    
    async def get_guest_statistics(self) -> SuccessResponse:
        """
        Lấy thống kê guest activities (admin).
        
        Returns:
            SuccessResponse với statistics data
        """
        stats = await self.guest_service.get_guest_statistics()
        
        return SuccessResponse(
            message="Lấy thống kê thành công",
            data=stats
        )