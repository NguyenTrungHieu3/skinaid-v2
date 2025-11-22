from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import require_admin
from app.modules.auth.services.token_cleanup_service import TokenCleanupService
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from typing import Union

router = APIRouter(prefix="/admin/cleanup", tags=["Admin - Cleanup"])


@router.get(
    "/stats",
    response_model=SuccessResponse[dict],
    summary="Xem thống kê cleanup"
)
async def get_cleanup_statistics(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Xem có bao nhiêu records cần cleanup
    """
    stats = await TokenCleanupService.get_cleanup_stats(db)
    return SuccessResponse(
        message="Đã lấy thành công thống kê cleanup",
        data=stats
    )


@router.get(
    "/stats/blacklist",
    response_model=SuccessResponse[dict],
    summary="Thống kê chi tiết token blacklist"
)
async def get_blacklist_statistics(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Thống kê chi tiết về token blacklist
    """
    stats = await TokenCleanupService.get_blacklist_stats(db)
    return SuccessResponse(
        message="Đã lấy thành công thống kê blacklist",
        data=stats
    )


@router.post(
    "/run/tokens",
    response_model=SuccessResponse[dict],
    summary="Cleanup expired blacklist tokens"
)
async def run_cleanup_tokens(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Xóa tất cả tokens trong blacklist đã hết hạn
    """
    deleted = await TokenCleanupService.cleanup_expired_tokens(db)
    return SuccessResponse(
        message=f"Đã xóa {deleted} tokens đã hết hạn",
        data={"deleted": deleted}
    )


@router.post(
    "/run/verifications",
    response_model=SuccessResponse[dict],
    summary="Cleanup verification tokens"
)
async def run_cleanup_verifications(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Xóa tất cả verification tokens đã hết hạn hoặc đã sử dụng
    """
    deleted = await TokenCleanupService.cleanup_old_verification_tokens(db)
    return SuccessResponse(
        message=f"Đã xóa {deleted} verification tokens",
        data={"deleted": deleted}
    )


@router.post(
    "/run/all",
    response_model=SuccessResponse[dict],
    summary="Chạy tất cả cleanup tasks"
)
async def run_full_cleanup(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Chạy tất cả cleanup tasks cùng lúc
    """
    result = await TokenCleanupService.cleanup_all(db)
    
    return SuccessResponse(
        message="Full cleanup hoàn tất",
        data=result
    )


@router.post(
    "/run/token-families",
    response_model=SuccessResponse[dict],
    summary="Cleanup expired token families"
)
async def run_cleanup_token_families(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Xóa tất cả token families đã hết hạn
    """
    deleted = await TokenCleanupService.cleanup_expired_token_families(db)
    return SuccessResponse(
        message=f"Đã xóa {deleted} token families đã hết hạn",
        data={"deleted": deleted}
    )


@router.post(
    "/users/{user_id}/revoke-all-tokens",
    response_model=Union[SuccessResponse[dict], ErrorResponse],
    summary="Admin force revoke all user tokens"
)
async def admin_revoke_user_tokens(
    user_id: str,
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Admin force revoke tất cả tokens của user
    """
    result = await TokenCleanupService.revoke_all_user_tokens(db, user_id)
    
    if not result["success"]:
        return ErrorResponse(
            message=result["message"],
            error_code="USER_NOT_FOUND",
            status_code=404
        )
    
    return SuccessResponse(
        message=f"Đã revoke tất cả tokens của user {user_id}",
        data=result
    )