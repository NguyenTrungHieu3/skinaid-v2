from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Cookie, Header
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Optional

from app.api.v1.deps import get_current_verified_user, get_db
from app.modules.ai.controllers.ai_controller import AIController

router = APIRouter(prefix="/ai")

async def get_session_id(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> Optional[UUID]:
    session_str = session_id or x_session_id

    if session_str:
        try:
            return UUID(session_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_id format")

    return None

@router.post("/analyze")
async def analyze_wound_image(
    file: UploadFile = File(..., description="Wound image (JPEG/PNG, max 5MB)"),
    current_user: Optional[dict] = Depends(get_current_verified_user),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = UUID(current_user.get('user_id')) if current_user and current_user.get('user_id') else None
    if not user_id and not session_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required or session_id must be provided"
        )

    result = await controller.analyze_image(
        file=file,
        user_id=user_id,
        session_id=session_id
    )

    return result

@router.get("/history")
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[dict] = Depends(get_current_verified_user),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = UUID(current_user.get('user_id')) if current_user and current_user.get('user_id') else None

    if not user_id and not session_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required or session_id must be provided"
        )

    result = await controller.get_analysis_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        offset=offset
    )

    return result

@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(
    analysis_id: UUID,
    current_user: Optional[dict] = Depends(get_current_verified_user),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = UUID(current_user.get('user_id')) if current_user and current_user.get('user_id') else None

    result = await controller.get_analysis_detail(
        analysis_id=analysis_id,
        user_id=user_id,
        session_id=session_id
    )

    return result

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: UUID,
    current_user: Optional[dict] = Depends(get_current_verified_user),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = UUID(current_user.get('user_id')) if current_user and current_user.get('user_id') else None

    result = await controller.delete_analysis(
        analysis_id=analysis_id,
        user_id=user_id,
        session_id=session_id
    )

    return result