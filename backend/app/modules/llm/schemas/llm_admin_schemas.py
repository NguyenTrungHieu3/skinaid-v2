from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Response schemas ─────────────────────────────────────────

class LLMConfigEnvDefaults(BaseModel):
    """Default values from .env for reference."""
    model_name: str
    temperature: float
    max_tokens: int
    top_k: Optional[int] = None


class LLMConfigResponse(BaseModel):
    """Single LLM configuration response."""
    id: str
    config_key: str
    display_name: str
    description: Optional[str] = None
    model_name: str
    temperature: float
    max_tokens: int
    top_k: int
    is_active: bool
    is_maintenance: bool
    maintenance_message: Optional[str] = None
    env_defaults: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LLMConfigListResponse(BaseModel):
    """List of all LLM configurations."""
    configs: List[LLMConfigResponse]
    total: int


class LLMAvailableModel(BaseModel):
    """Available model for selection."""
    id: str
    name: str
    description: str
    tier: str = Field(description="low | mid | high")


class LLMAvailableModelsResponse(BaseModel):
    """List of available LLM models."""
    models: List[LLMAvailableModel]


# ── Request schemas (Phase 2) ────────────────────────────────

class SwitchModelRequest(BaseModel):
    """Request to switch LLM model for a config."""
    new_model: str = Field(
        ...,
        description="ID model mới (ví dụ: gpt-4.1-mini, gpt-4.1-nano)",
        min_length=1,
        max_length=100,
    )
    reason: Optional[str] = Field(
        default=None,
        description="Lý do đổi model",
        max_length=500,
    )


class SetMaintenanceRequest(BaseModel):
    """Request to enable/disable maintenance mode."""
    enabled: bool = Field(..., description="True = bật bảo trì, False = tắt bảo trì")
    message: Optional[str] = Field(
        default=None,
        description="Thông báo bảo trì hiển thị cho users",
        max_length=500,
    )


class SwitchModelResponse(BaseModel):
    """Response after model switch."""
    config_key: str
    old_model: str
    new_model: str
    is_maintenance: bool
    message: str


# ── Request schemas (Phase 3) ────────────────────────────────

class ToggleActiveRequest(BaseModel):
    """Request to activate/deactivate a LLM config."""
    is_active: bool = Field(..., description="True = kích hoạt, False = tắt")
    reason: Optional[str] = Field(
        default=None,
        description="Lý do kích hoạt/tắt",
        max_length=500,
    )


# ── Request schemas (Phase 4) ────────────────────────────────

class UpdateParamsRequest(BaseModel):
    """Request to update LLM parameters (temperature, max_tokens, top_k)."""
    temperature: Optional[float] = Field(
        default=None,
        description="Nhiệt độ tạo sinh (0.0 - 2.0)",
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Số token tối đa cho output (100 - 16000)",
        ge=100,
        le=16000,
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Số lượng kết quả top-k cho RAG (1 - 20)",
        ge=1,
        le=20,
    )
    reason: Optional[str] = Field(
        default=None,
        description="Lý do thay đổi tham số",
        max_length=500,
    )


# ── Schemas (Phase 5) ────────────────────────────────────────

class TestPromptRequest(BaseModel):
    """Request to test LLM with a custom prompt."""
    prompt: str = Field(
        ...,
        description="Prompt test gửi đến LLM",
        min_length=1,
        max_length=2000,
    )
    model_override: Optional[str] = Field(
        default=None,
        description="Dùng model khác để test (nếu không chỉ định, dùng model hiện tại)",
        max_length=100,
    )


class TestPromptResponse(BaseModel):
    """Response from LLM test."""
    config_key: str
    model_used: str
    prompt: str
    response: str
    tokens_used: int
    response_time_ms: int


# ── Schemas (Phase 6) ────────────────────────────────────────

class ChangeLogEntry(BaseModel):
    """Single audit log entry."""
    id: str
    config_key: str
    display_name: str
    change_type: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    changed_by: Optional[str] = None
    changed_by_email: Optional[str] = None
    created_at: str


class ChangeLogListResponse(BaseModel):
    """List of change log entries."""
    logs: List[ChangeLogEntry]
    total: int


# ── Schemas (Phase 7) ────────────────────────────────────────

class UsageConfigStats(BaseModel):
    """Per-config usage statistics."""
    config_key: str
    display_name: str
    total_requests: int
    success_count: int
    error_count: int
    total_tokens: int
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    avg_response_time_ms: float
    last_used_at: Optional[str] = None


class BudgetInfo(BaseModel):
    """Budget and cost tracking info."""
    monthly_budget_usd: float
    price_per_1k_input_tokens: float
    price_per_1k_output_tokens: float
    currency: str = "USD"
    monthly_prompt_tokens: int = 0
    monthly_completion_tokens: int = 0
    monthly_total_tokens: int = 0
    monthly_estimated_cost: float = 0.0
    budget_usage_percent: float = 0.0


class UsageStatsResponse(BaseModel):
    """Aggregated usage statistics."""
    total_requests: int
    total_tokens: int
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    estimated_cost: float = 0.0
    avg_response_time_ms: float
    success_rate: float
    per_config: List[UsageConfigStats]
    period_days: int
    budget: Optional[BudgetInfo] = None


# ── Schemas (Phase 8): Budget ────────────────────────────────

class BudgetSettingsResponse(BaseModel):
    """Budget settings response."""
    monthly_budget_usd: float
    price_per_1k_input_tokens: float
    price_per_1k_output_tokens: float
    currency: str
    updated_at: Optional[str] = None


class UpdateBudgetRequest(BaseModel):
    """Request to update budget settings."""
    monthly_budget_usd: Optional[float] = Field(
        default=None,
        description="Budget hàng tháng (USD). 0 = không giới hạn.",
        ge=0,
    )
    price_per_1k_input_tokens: Optional[float] = Field(
        default=None,
        description="Giá / 1K input tokens (USD)",
        ge=0,
    )
    price_per_1k_output_tokens: Optional[float] = Field(
        default=None,
        description="Giá / 1K output tokens (USD)",
        ge=0,
    )
