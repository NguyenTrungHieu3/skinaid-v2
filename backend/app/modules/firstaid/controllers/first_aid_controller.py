from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.modules.firstaid.services.first_aid_service import FirstAidService
import logging

logger = logging.getLogger(__name__)

class FirstAidController:
    """Controller xử lý các yêu cầu first aid"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)

    async def get_first_aid_guide(
        self,
        wound_type: str,
        severity: str
    ) -> Dict[str, Any]:

        try:
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity)

            if not guide:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy hướng dẫn sơ cứu cho {wound_type}/{severity}"
                )

            return {
                "success": True,
                "data": guide
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get first aid guide: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lấy hướng dẫn sơ cứu"
            )

    async def get_available_wound_types(self) -> Dict[str, Any]:
        try:
            wound_types = await self.first_aid_service.get_available_wound_types()

            return {
                "success": True,
                "data": wound_types
            }

        except Exception as e:
            logger.error(f"Failed to get available wound types: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể lấy loại vết thương"
            )

    async def search_first_aid_guides(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:

        try:
            guides = await self.first_aid_service.search_first_aid_guides(wound_type, severity, limit)

            return {
                "success": True,
                "data": guides
            }

        except Exception as e:
            logger.error(f"Failed to search first aid guides: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể tìm kiếm hướng dẫn sơ cứu"
            )