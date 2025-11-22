"""
Logging utilities for sanitizing sensitive data before logging.
"""

from typing import Dict, Any, List, Set
import copy


# Fields that should be completely redacted
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

# Fields that should be partially masked (show first/last few characters)
MASKABLE_FIELDS: Set[str] = {
    "email",
    "phone",
    "phone_number",
}


def sanitize_for_logging(data: Any, redact_sensitive: bool = True, mask_email: bool = True) -> Any:
    """
    Sanitize data structure for safe logging by removing or masking sensitive information.
    
    Args:
        data: The data to sanitize (dict, list, or primitive)
        redact_sensitive: Whether to redact sensitive fields (passwords, tokens, etc.)
        mask_email: Whether to mask email addresses
    
    Returns:
        Sanitized copy of the data
    
    Examples:
        >>> sanitize_for_logging({"email": "user@example.com", "password": "secret123"})
        {"email": "u***@example.com", "password": "***REDACTED***"}
    """
    if data is None:
        return None
    
    # Handle dictionaries
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Redact sensitive fields
            if redact_sensitive and any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            # Mask maskable fields
            elif mask_email and any(maskable in key_lower for maskable in MASKABLE_FIELDS):
                sanitized[key] = _mask_value(value, key_lower)
            # Recursively sanitize nested structures
            else:
                sanitized[key] = sanitize_for_logging(value, redact_sensitive, mask_email)
                
        return sanitized
    
    # Handle lists
    elif isinstance(data, (list, tuple)):
        return [sanitize_for_logging(item, redact_sensitive, mask_email) for item in data]
    
    # Return primitives as-is
    else:
        return data


def _mask_value(value: Any, field_type: str) -> str:
    """
    Mask a value based on its field type.
    
    Args:
        value: The value to mask
        field_type: The type/name of the field (lowercased)
    
    Returns:
        Masked string representation
    """
    if not isinstance(value, str):
        value = str(value)
    
    if len(value) == 0:
        return value
    
    # Email masking
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
    
    # Phone masking
    elif "phone" in field_type:
        if len(value) <= 4:
            return "***" + value[-2:]
        else:
            return "***" + value[-4:]
    
    # Default masking
    else:
        if len(value) <= 4:
            return value[0] + "***"
        else:
            return value[:2] + "***" + value[-2:]


def sanitize_user_data(user_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function specifically for sanitizing user data before logging.
    
    Args:
        user_dict: User data dictionary
    
    Returns:
        Sanitized user data safe for logging
    
    Example:
        >>> user = {"email": "admin@example.com", "password": "secret", "role": "admin"}
        >>> sanitize_user_data(user)
        {"email": "a***@example.com", "password": "***REDACTED***", "role": "admin"}
    """
    return sanitize_for_logging(user_dict, redact_sensitive=True, mask_email=True)


def log_admin_action(action: str, target: str, details: Dict[str, Any] = None) -> str:
    """
    Format admin action for logging with sanitized details.
    
    Args:
        action: The action being performed (e.g., "CREATE_USER", "UPDATE_USER")
        target: The target of the action (e.g., user ID, email)
        details: Additional details to log (will be sanitized)
    
    Returns:
        Formatted log message
    
    Example:
        >>> log_admin_action("CREATE_USER", "user@example.com", {"role": "admin", "password": "secret"})
        "[ADMIN_ACTION] CREATE_USER target=user@example.com details={'role': 'admin', 'password': '***REDACTED***'}"
    """
    if details:
        sanitized_details = sanitize_for_logging(details)
        return f"[ADMIN_ACTION] {action} target={target} details={sanitized_details}"
    else:
        return f"[ADMIN_ACTION] {action} target={target}"
