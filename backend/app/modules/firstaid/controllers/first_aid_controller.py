from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.modules.firstaid.services.first_aid_service import FirstAidService
import logging

logger = logging.getLogger(__name__)

class FirstAidController:
    @staticmethod
    async def get_first_aid_guide(
        db: AsyncSession,
        wound_type: str,
        severity: str
    ) -> Dict[str, Any]:
        
        try:
            service = FirstAidService(db)
            guide = await service.get_first_aid_guide(wound_type, severity)

            if not guide:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No first aid guide found for {wound_type}/{severity}"
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
                detail="Failed to retrieve first aid guide"
            )

    @staticmethod
    async def get_available_wound_types(db: AsyncSession) -> Dict[str, Any]:
        try:
            service = FirstAidService(db)
            wound_types = await service.get_available_wound_types()

            return {
                "success": True,
                "data": wound_types
            }

        except Exception as e:
            logger.error(f"Failed to get available wound types: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve wound types"
            )

    @staticmethod
    async def search_first_aid_guides(
        db: AsyncSession,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        
        try:
            service = FirstAidService(db)
            guides = await service.search_first_aid_guides(wound_type, severity, limit)

            return {
                "success": True,
                "data": guides
            }

        except Exception as e:
            logger.error(f"Failed to search first aid guides: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search first aid guides"
            )