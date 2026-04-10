"""Shared utilities for FirstAid module."""
from typing import Any, Dict, List, Optional, TypeVar
from sqlalchemy import func

T = TypeVar('T')


def wrap_jsonb_list(items: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    """Wrap a list in JSONB format with 'items' key."""
    return {"items": items} if items else None


def unwrap_jsonb_list(data: Optional[Any]) -> List[str]:
    """Extract list from JSONB 'items' field."""
    if not data:
        return []
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get('items', [])
    return []


def normalize_field_comparison(field: T, value: str):
    """Create case-insensitive comparison for SQLAlchemy field."""
    return func.lower(field) == func.lower(value)


def build_active_filter(model_class: T):
    """Build standard active and not deleted filter conditions."""
    return [
        model_class.is_active == True,
        model_class.is_deleted == False,
    ]
