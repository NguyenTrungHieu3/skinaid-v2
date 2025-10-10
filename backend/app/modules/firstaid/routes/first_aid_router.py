from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.modules.firstaid.controllers.first_aid_controller import FirstAidController
from app.modules.firstaid.schemas.first_aid_schemas import (
    FirstAidGuideResponse,
    WoundTypeResponse,
    FirstAidSearchResponse
)
from app.api.v1.deps import get_db, get_current_active_user

router = APIRouter(prefix="/first-aid", tags=["First Aid"])

@router.get("/guide/{wound_type}/{severity}", response_model=dict)
async def get_first_aid_guide(
    wound_type: str,
    severity: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    controller = FirstAidController(db)
    return await controller.get_first_aid_guide(wound_type, severity)

@router.get("/wound-types", response_model=dict)
async def get_available_wound_types(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    controller = FirstAidController(db)
    return await controller.get_available_wound_types()

@router.get("/search", response_model=dict)
async def search_first_aid_guides(
    wound_type: Optional[str] = Query(None, description="Filter by wound type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(20, description="Maximum number of results", le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    controller = FirstAidController(db)
    return await controller.search_first_aid_guides(wound_type, severity, limit)