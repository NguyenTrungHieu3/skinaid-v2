from typing import Dict, Any, Set
import copy

SENSITIVE_FIELDS: Set[str] = {
    "password",
    "password_hash",
    "hashed_password",
    "new_password",
    "old_password",
    "current_password",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "private_key",
    "credit_card",
    "cvv",
    "ssn",
}

MASKABLE_FIELDS: Set[str] = {
    "email",
    "phone",
    "phone_number",
}


def sanitize_for_logging(data: Any, redact_sensitive: bool = True, mask_email: bool = True) -> Any:
    if data is None:
        return None

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()

            if redact_sensitive and any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            elif mask_email and any(maskable in key_lower for maskable in MASKABLE_FIELDS):
                sanitized[key] = _mask_value(value, key_lower)
            else:
                sanitized[key] = sanitize_for_logging(value, redact_sensitive, mask_email)

        return sanitized

    elif isinstance(data, (list, tuple)):
        return [sanitize_for_logging(item, redact_sensitive, mask_email) for item in data]

    else:
        return data


def _mask_value(value: Any, field_type: str) -> str:
    if not isinstance(value, str):
        value = str(value)

    if len(value) == 0:
        return value

    if "email" in field_type:
        if "@" in value:
            local, domain = value.rsplit("@", 1)
            if len(local) <= 2:
                masked_local = local[0] + "*"
            else:
                masked_local = local[0] + "***"
            return f"{masked_local}@{domain}"
        else:
            return value[:2] + "***"

    elif "phone" in field_type:
        if len(value) <= 4:
            return "***" + value[-2:]
        else:
            return "***" + value[-4:]

    else:
        if len(value) <= 4:
            return value[0] + "***"
        else:
            return value[:2] + "***" + value[-2:]


def sanitize_user_data(user_dict: Dict[str, Any]) -> Dict[str, Any]:
    return sanitize_for_logging(user_dict, redact_sensitive=True, mask_email=True)


def log_admin_action(action: str, target: str, details: Dict[str, Any] = None) -> str:
    if details:
        sanitized_details = sanitize_for_logging(details)
        return f"[ADMIN_ACTION] {action} target={target} details={sanitized_details}"
    else:
        return f"[ADMIN_ACTION] {action} target={target}"
