from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.dependencies.database import get_db
from app.modules.users.models import User
from app.modules.llm.services.llm_config_service import LLMConfigService
from app.modules.llm.schemas.llm_admin_schemas import (
    LLMConfigListResponse,
    LLMConfigResponse,
    LLMAvailableModelsResponse,
    LLMAvailableModel,
    SwitchModelRequest,
    SetMaintenanceRequest,
    SwitchModelResponse,
    ToggleActiveRequest,
    UpdateParamsRequest,
    TestPromptRequest,
    TestPromptResponse,
    ChangeLogListResponse,
    UsageStatsResponse,
    BudgetSettingsResponse,
    UpdateBudgetRequest,
)
from app.shared.response import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/llm")


def _get_config_service(db: AsyncSession = Depends(get_db)) -> LLMConfigService:
    return LLMConfigService(db)


# ── Phase 1: Read endpoints ─────────────────────────────────

@router.get(
    "/configs",
    response_model=SuccessResponse[LLMConfigListResponse],
    summary="Lấy tất cả cấu hình LLM",
    description="Trả về danh sách tất cả LLM configurations (synthesis, chatbot_advisor, chatbot_guide) với giá trị hiện tại và .env defaults.",
)
async def get_all_configs(
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    configs = await service.get_all_configs()
    return SuccessResponse(
        message="Lấy danh sách cấu hình LLM thành công",
        data=LLMConfigListResponse(
            configs=[LLMConfigResponse(**c) for c in configs],
            total=len(configs),
        ),
    )


@router.get(
    "/configs/{config_key}",
    response_model=SuccessResponse[LLMConfigResponse],
    summary="Lấy chi tiết 1 cấu hình LLM",
    description="Trả về chi tiết cấu hình LLM theo config_key (synthesis / chatbot_advisor / chatbot_guide).",
)
async def get_config(
    config_key: str,
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    config = await service.get_config(config_key)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config '{config_key}' không tồn tại")

    return SuccessResponse(
        message="Lấy cấu hình LLM thành công",
        data=LLMConfigResponse(**config),
    )


@router.get(
    "/available-models",
    response_model=SuccessResponse[LLMAvailableModelsResponse],
    summary="Danh sách model LLM khả dụng",
    description="Trả về danh sách các model OpenAI có thể chọn.",
)
async def get_available_models(
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    models = service.get_available_models()
    return SuccessResponse(
        message="Lấy danh sách model khả dụng thành công",
        data=LLMAvailableModelsResponse(
            models=[LLMAvailableModel(**m) for m in models],
        ),
    )


# ── Phase 2: Switch model & Maintenance ─────────────────────

@router.put(
    "/configs/{config_key}/model",
    response_model=SuccessResponse[SwitchModelResponse],
    summary="Đổi model LLM",
    description="Chuyển sang model LLM khác. Hệ thống tự động bật bảo trì → đổi model → tắt bảo trì.",
)
async def switch_model(
    config_key: str,
    body: SwitchModelRequest,
    service: LLMConfigService = Depends(_get_config_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        result = await service.switch_model(
            config_key=config_key,
            new_model=body.new_model,
            admin_id=current_user.user_id,
            reason=body.reason,
        )
        return SuccessResponse(
            message=result["message"],
            data=SwitchModelResponse(**result),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/configs/{config_key}/maintenance",
    response_model=SuccessResponse[LLMConfigResponse],
    summary="Bật/tắt chế độ bảo trì",
    description="Bật hoặc tắt chế độ bảo trì cho một cấu hình LLM. Khi bảo trì, LLM sẽ trả lỗi thân thiện.",
)
async def set_maintenance(
    config_key: str,
    body: SetMaintenanceRequest,
    service: LLMConfigService = Depends(_get_config_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        config = await service.set_maintenance(
            config_key=config_key,
            enabled=body.enabled,
            message=body.message,
            admin_id=current_user.user_id,
        )
        status_text = "bật" if body.enabled else "tắt"
        return SuccessResponse(
            message=f"Đã {status_text} chế độ bảo trì cho '{config_key}'",
            data=LLMConfigResponse(**config),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Phase 3: Activate / Deactivate ───────────────────────────

@router.put(
    "/configs/{config_key}/toggle",
    response_model=SuccessResponse[LLMConfigResponse],
    summary="Kích hoạt / Tắt cấu hình LLM",
    description="Kích hoạt hoặc tắt một cấu hình LLM. Khi tắt, hệ thống sẽ không gọi LLM mà fallback sang dữ liệu có sẵn.",
)
async def toggle_active(
    config_key: str,
    body: ToggleActiveRequest,
    service: LLMConfigService = Depends(_get_config_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        config = await service.toggle_active(
            config_key=config_key,
            is_active=body.is_active,
            admin_id=current_user.user_id,
            reason=body.reason,
        )
        status_text = "kích hoạt" if body.is_active else "tắt"
        return SuccessResponse(
            message=f"Đã {status_text} cấu hình '{config_key}'",
            data=LLMConfigResponse(**config),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Phase 4: Update Parameters ───────────────────────────────

@router.put(
    "/configs/{config_key}/params",
    response_model=SuccessResponse[LLMConfigResponse],
    summary="Chỉnh tham số LLM",
    description="Cập nhật tham số LLM: temperature, max_tokens, top_k. Chỉ cần gửi các tham số muốn thay đổi.",
)
async def update_params(
    config_key: str,
    body: UpdateParamsRequest,
    service: LLMConfigService = Depends(_get_config_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        config = await service.update_params(
            config_key=config_key,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            top_k=body.top_k,
            admin_id=current_user.user_id,
            reason=body.reason,
        )
        return SuccessResponse(
            message=f"Đã cập nhật tham số cho '{config_key}'",
            data=LLMConfigResponse(**config),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Phase 5: Test Prompt ─────────────────────────────────

@router.post(
    "/configs/{config_key}/test",
    response_model=SuccessResponse[TestPromptResponse],
    summary="Test thử model LLM",
    description="Gửi một prompt test đến LLM và nhận kết quả. Có thể chỉ định model khác để so sánh.",
)
async def test_prompt(
    config_key: str,
    body: TestPromptRequest,
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        result = await service.test_prompt(
            config_key=config_key,
            prompt=body.prompt,
            model_override=body.model_override,
        )
        return SuccessResponse(
            message="Test thành công",
            data=TestPromptResponse(**result),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Phase 6: Change Logs (Audit) ───────────────────────────

@router.get(
    "/change-logs",
    response_model=SuccessResponse[ChangeLogListResponse],
    summary="Xem lịch sử thay đổi cấu hình LLM",
    description="Lấy danh sách các thay đổi cấu hình LLM, có hỗ trợ lọc theo config_key và phân trang.",
)
async def get_change_logs(
    config_key: str | None = None,
    limit: int = 50,
    offset: int = 0,
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    result = await service.get_change_logs(
        config_key=config_key,
        limit=min(limit, 100),  # Cap at 100
        offset=max(offset, 0),
    )
    return SuccessResponse(
        message="Lấy lịch sử thay đổi thành công",
        data=ChangeLogListResponse(**result),
    )


# ── Phase 7: Usage Statistics ─────────────────────────────

@router.get(
    "/usage-stats",
    response_model=SuccessResponse[UsageStatsResponse],
    summary="Thống kê sử dụng LLM",
    description="Lấy thống kê tổng hợp về sử dụng LLM: tokens, requests, response time.",
)
async def get_usage_stats(
    days: int = 30,
    config_key: str | None = None,
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    result = await service.get_usage_stats(
        period_days=min(max(days, 1), 365),
        config_key=config_key,
    )
    return SuccessResponse(
        message="Lấy thống kê thành công",
        data=UsageStatsResponse(**result),
    )


# ── Phase 8: Budget Settings ─────────────────────────────

@router.get(
    "/budget",
    response_model=SuccessResponse[BudgetSettingsResponse],
    summary="Lấy cài đặt budget",
    description="Lấy cấu hình budget và giá token hiện tại.",
)
async def get_budget(
    service: LLMConfigService = Depends(_get_config_service),
    _current_user: User = Depends(require_admin),
) -> SuccessResponse:
    result = await service.get_budget_settings()
    return SuccessResponse(
        message="Lấy cài đặt budget thành công",
        data=BudgetSettingsResponse(**result),
    )


@router.put(
    "/budget",
    response_model=SuccessResponse[BudgetSettingsResponse],
    summary="Cập nhật budget",
    description="Cập nhật budget hàng tháng và giá token.",
)
async def update_budget(
    body: UpdateBudgetRequest,
    service: LLMConfigService = Depends(_get_config_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    try:
        result = await service.update_budget_settings(
            user_id=current_user.user_id,
            monthly_budget_usd=body.monthly_budget_usd,
            price_per_1k_input_tokens=body.price_per_1k_input_tokens,
            price_per_1k_output_tokens=body.price_per_1k_output_tokens,
        )
        return SuccessResponse(
            message="Cập nhật budget thành công",
            data=BudgetSettingsResponse(**result),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
