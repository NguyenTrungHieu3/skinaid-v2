import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from app.modules.audit.models.audit_log import AuditLog
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.schemas.api import AuditLogFilterParams

logger = logging.getLogger(__name__)

# ── Action → log_type mapping ──────────────────────────────
_ADMIN_ACTIONS = {
    "activate_user", "deactivate_user",
    "upload_ai_model", "activate_ai_model", "rollback_ai_model", "delete_ai_model",
    "update_llm_config", "toggle_vision_fallback", "rollback_llm_config",
}

_SYSTEM_ERROR_ACTIONS = {
    "ai_model_error", "llm_api_error", "model_load_error", "rag_error",
}

_USER_ACTIVITY_ACTIONS = {
    "user_login", "user_login_failed", "user_logout",
    "register", "wound_scan", "upload_image",
    "refresh_token", "password_reset", "change_password",
}


def _infer_log_type(action: str) -> str:
    """Auto-detect log_type from action name."""
    if action in _ADMIN_ACTIONS:
        return "admin_action"
    if action in _SYSTEM_ERROR_ACTIONS:
        return "system_error"
    return "user_activity"


def _infer_level(action: str, success: bool, error_message: Optional[str]) -> str:
    """Auto-detect severity level."""
    if action in _SYSTEM_ERROR_ACTIONS:
        return "error"
    if not success and error_message:
        return "error"
    if not success:
        return "warning"
    if action == "user_login_failed":
        return "warning"
    return "info"


def _generate_description(
    action: str,
    success: bool,
    resource_type: Optional[str],
    resource_id: Optional[str],
    error_message: Optional[str],
) -> str:
    """Auto-generate a human-readable description if none supplied."""
    action_labels = {
        "user_login": "User logged in",
        "user_login_failed": "Failed login attempt",
        "user_logout": "User logged out",
        "register": "New user registered",
        "wound_scan": "Wound image scanned",
        "upload_image": "Image uploaded for analysis",
        "refresh_token": "Token refreshed",
        "password_reset": "Password reset",
        "change_password": "Password changed",
        "activate_user": "Admin activated user account",
        "deactivate_user": "Admin deactivated user account",
        "upload_ai_model": "AI model uploaded",
        "activate_ai_model": "AI model activated",
        "rollback_ai_model": "AI model rolled back",
        "delete_ai_model": "AI model deleted",
        "ai_model_error": "AI model error occurred",
        "llm_api_error": "LLM API error occurred",
        "model_load_error": "Model loading error",
        "rag_error": "RAG retrieval error",
    }

    base = action_labels.get(action, f"Action: {action}")

    if resource_type and resource_id:
        base += f" [{resource_type}: {resource_id[:36]}]"

    if not success and error_message:
        base += f" — Error: {error_message[:120]}"

    return base


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def log_event(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        success: bool = True,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        is_guest: bool = False,
        guest_session_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        # ── US-LOG-01 new params ──
        log_type: Optional[str] = None,
        level: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        If log_type / level / description are not provided, they are
        auto-inferred from the action name and success flag.
        """
        if error_message and len(error_message) > 500:
            error_message = error_message[:497] + "..."
        if user_agent and len(user_agent) > 500:
            user_agent = user_agent[:497] + "..."

        # Auto-infer when caller doesn't specify
        resolved_log_type = log_type or _infer_log_type(action)
        resolved_level = level or _infer_level(action, success, error_message)
        resolved_description = description or _generate_description(
            action, success, resource_type, resource_id, error_message
        )

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            log_type=resolved_log_type,
            level=resolved_level,
            description=resolved_description,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            is_guest=is_guest,
            guest_session_id=guest_session_id,
            details=details
        )

        return await self.repository.create(audit_log)

    async def get_audit_logs(
        self,
        filters: AuditLogFilterParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        offset = (filters.page - 1) * filters.limit
        return await self.repository.get_audit_logs(
            user_id=filters.user_id,
            action=filters.action,
            resource_type=filters.resource_type,
            success=filters.success,
            is_guest=filters.is_guest,
            search=filters.search,
            role_name=filters.role_name,
            start_date=filters.start_date,
            end_date=filters.end_date,
            log_type=filters.log_type,
            level=filters.level,
            limit=filters.limit,
            offset=offset
        )

    async def get_audit_stats(self) -> Dict[str, Any]:
        return await self.repository.get_audit_stats()

