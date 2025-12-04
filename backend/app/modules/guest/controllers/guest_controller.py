from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.modules.guest.services.guest_service import GuestService
from app.shared.schemas.response import SuccessResponse
from app.modules.audit.services.audit_service import AuditService
from fastapi import HTTPException

class GuestController:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
        self.guest_service = GuestService(db)
    
    async def create_guest_session(
        self, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SuccessResponse:
        """
        Tạo guest session mới
        """
        session = await self.guest_service.create_guest_session(
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        await self.audit_service.log_event(
            action="guest_session_created",
            resource_type="guest_session",
            resource_id=str(session["session_id"]),
            is_guest=True,
            guest_session_id=session["session_id"],
            success=True,
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
        Lấy thông tin guest session
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
        Lấy thống kê guest activities (admin)
        """
        stats = await self.guest_service.get_guest_statistics()
        
        return SuccessResponse(
            message="Lấy thống kê thành công",
            data=stats
        )

    async def claim_analysis(
        self,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> SuccessResponse:
        """
        User nhận quyền sở hữu analysis từ guest session
        """
        success = await self.guest_service.claim_analysis(analysis_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="Phân tích không tồn tại hoặc đã thuộc về người dùng khác"
            )
            
        await self.audit_service.log_event(
            action="analysis_claimed",
            resource_type="wound_analysis",
            resource_id=str(analysis_id),
            user_id=user_id,
            success=True
        )
        
        return SuccessResponse(
            message="Lưu kết quả phân tích vào lịch sử thành công",
            data={"analysis_id": analysis_id, "user_id": user_id}
        )