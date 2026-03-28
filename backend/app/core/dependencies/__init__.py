from .database import get_db
from .oauth2 import oauth2_scheme, oauth2_scheme_optional
from .token import (
    extract_token,
    decode_and_verify_token,
    is_token_blacklisted,
    revoke_token,
)
from .user import (
    get_user_by_id,
    check_email_verified,
    check_user_has_role,
    check_user_has_permission,
    get_user_roles,
    get_user_permissions,
)

from .access_control import (
    get_token,
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    allow_access,
    require_role,
    require_permission,
    require_any_permissions,
    require_all_permissions,
    allow_guest,
    require_auth,
    require_verified,
    guest_only,
    require_admin,
    require_user,
    require_admin_or_moderator,
    require_upload,
    require_ai_analyze,
    require_manage_users,
    require_manage_firstaid,
    require_read_all_history,
    require_read_logs,
)

__all__ = [
    # Database
    "get_db",
    # OAuth2
    "oauth2_scheme",
    "oauth2_scheme_optional",
    # Token
    "extract_token",
    "decode_and_verify_token",
    "is_token_blacklisted",   # (jti: str) → bool  [Redis]
    "revoke_token",           # (token: str, user_id?) → bool  [Redis]
    # User
    "get_user_by_id",
    "check_email_verified",
    "check_user_has_role",
    "check_user_has_permission",
    "get_user_roles",
    "get_user_permissions",
    # Access control
    "get_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "allow_access",
    "require_role",
    "require_permission",
    "require_any_permissions",
    "require_all_permissions",
    # Shortcuts
    "allow_guest",
    "require_auth",
    "require_verified",
    "guest_only",
    "require_admin",
    "require_user",
    "require_admin_or_moderator",
    "require_upload",
    "require_ai_analyze",
    "require_manage_users",
    "require_manage_firstaid",
    "require_read_all_history",
    "require_read_logs",
]