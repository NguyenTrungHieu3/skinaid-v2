USER_REGISTER_SUCCESS_MSG = "Registration successful! You can login now."
USER_LOGIN_SUCCESS_MSG = "Login successful"
USER_LOGOUT_SUCCESS_MSG = "Logout successful"
PASSWORD_RESET_SUCCESS_MSG = "Password has been updated successfully."
TOKEN_REFRESH_SUCCESS_MSG = "Token refreshed successfully"
AUTH_HEALTH_CHECK_MSG = "Auth service is operating normally"
PASSWORD_RESET_REQUEST_PROCESSING_MSG = "If the email exists, a password reset link has been sent to your email address."
PASSWORD_RESET_PROCESSED_MSG = "Password reset request processed"
PASSWORD_RESET_SUCCESSFUL_MSG = "Password reset successful"
SESSION_TERMINATED_MSG = "Session terminated"
LOGOUT_ALL_DEVICES_SUCCESS_MSG = "Logged out from all devices successfully"
ALL_TOKENS_REVOKED_MSG = "All tokens have been revoked. Please login again."
PASSWORD_CHANGED_ALL_DEVICES_LOGOUT_MSG = "Password changed successfully. All devices have been logged out."
PASSWORD_CHANGED_LOGIN_AGAIN_MSG = "Password changed. Please login again on all devices."
LOGOUT_SUCCESS_TOKENS_REVOKED_MSG = "Logout successful. {revoked_count} tokens revoked."

AUTH_INVALID_TOKEN_MSG = "Invalid or expired token"
AUTH_INVALID_TOKEN_TYPE_MSG = "Invalid token type"
AUTH_USER_NOT_FOUND_MSG = "User not found"
AUTH_INVALID_REFRESH_TOKEN_MSG = "Invalid refresh token"
AUTH_RESET_PASSWORD_FAILED_MSG = "Failed to reset password"
AUTH_CHANGE_PASSWORD_FAILED_MSG = "Failed to change password"
AUTH_TOKEN_REUSE_DETECTED_MSG = "Token reuse detected"
AUTH_TOKEN_REVOKED_MSG = "Token has been revoked"

PASSWORD_REQUIREMENTS = [
    "At least 8 characters",
    "Contains uppercase",
    "Contains lowercase",
    "Contains number",
    "Contains special character"
]

USER_INVALID_DATA_MSG = "Invalid user data"

AI_ANALYSIS_SUCCESS_MSG = "Wound analysis successful"
AI_HISTORY_SUCCESS_MSG = "Analysis history retrieved successfully"
AI_DETAIL_SUCCESS_MSG = "Analysis details retrieved successfully"
AI_DELETE_SUCCESS_MSG = "Analysis deleted successfully"

AI_MISSING_IDENTIFIER_MSG = "Missing identifier. Please provide user_id or session_id"
AI_MULTIPLE_IDENTIFIERS_MSG = "Provide user_id OR session_id, not both"
AI_INVALID_FILE_MSG = "Invalid file. Please upload a valid image"
AI_ANALYSIS_NOT_FOUND_MSG = "Analysis not found"
AI_ACCESS_DENIED_MSG = "You do not have permission to access this analysis"
AI_HISTORY_ERROR_MSG = "Failed to retrieve analysis history"
AI_DETAIL_ERROR_MSG = "Failed to retrieve analysis details"
AI_DELETE_ERROR_MSG = "Failed to delete analysis"

WOUND_TYPES_SUCCESS_MSG = "Wound types retrieved successfully"
FIRSTAID_STATISTICS_SUCCESS_MSG = "First aid statistics retrieved successfully"
FIRSTAID_CREATE_SUCCESS_MSG = "First aid guide created successfully"
FIRSTAID_UPDATE_SUCCESS_MSG = "First aid guide updated successfully"
FIRSTAID_DELETE_SUCCESS_MSG = "First aid guide deleted successfully"
FIRSTAID_GET_SUCCESS_MSG = "First aid guide retrieved successfully"

FIRSTAID_GUIDE_CREATED_SUCCESS_MSG = "First aid guide created successfully"
FIRSTAID_GUIDE_UPDATED_SUCCESS_MSG = "First aid guide updated successfully"
FIRSTAID_GUIDE_DELETED_SUCCESS_MSG = "First aid guide deleted successfully"
FIRSTAID_GUIDE_FOUND_MSG = "First aid guide retrieved successfully"

FIRSTAID_GUIDE_FOUND_FOR_MSG = "First aid guide retrieved successfully for {wound_type}/{severity}"
FIRSTAID_GUIDE_NOT_FOUND_FOR_MSG = "First aid guide not found for wound type '{wound_type}' severity '{severity}'"
FIRSTAID_GUIDE_NOT_FOUND_WITH_SUBTYPE_MSG = "First aid guide not found for wound type '{wound_type}' severity '{severity}' with sub_type '{sub_type}'"
FIRSTAID_GUIDES_FOUND_COUNT_MSG = "Found {count} first aid guides"
FIRSTAID_GUIDE_AVAILABLE_FOR_MSG = "First aid guide for {wound_type}/{severity} is available"
FIRSTAID_GUIDE_AVAILABLE_WITH_SUBTYPE_MSG = "First aid guide for {wound_type}/{severity} with sub_type '{sub_type}' is available"
FIRSTAID_GUIDE_NOT_AVAILABLE_FOR_MSG = "First aid guide for {wound_type}/{severity} is not available"
FIRSTAID_GUIDE_NOT_AVAILABLE_WITH_SUBTYPE_MSG = "First aid guide for {wound_type}/{severity} with sub_type '{sub_type}' is not available"

FIRSTAID_STATISTICS_ERROR_MSG = "Failed to retrieve first aid statistics"
FIRSTAID_GUIDE_ERROR_MSG = "Failed to retrieve first aid guide"
WOUND_TYPES_ERROR_MSG = "Failed to retrieve wound types"
FIRSTAID_SEARCH_ERROR_MSG = "Failed to search first aid guides"
FIRSTAID_VALIDATION_ERROR_MSG = "Failed to validate guide availability"

FIRSTAID_GUIDE_CREATE_ERROR_MSG = "Failed to create first aid guide"
FIRSTAID_GUIDE_UPDATE_ERROR_MSG = "Failed to update first aid guide"
FIRSTAID_GUIDE_DELETE_ERROR_MSG = "Failed to delete first aid guide"
FIRSTAID_GUIDE_NOT_FOUND_MSG = "First aid guide not found"

AUDIT_LOGS_SUCCESS_MSG = "Audit logs retrieved successfully"
AUDIT_STATS_SUCCESS_MSG = "Audit statistics retrieved successfully"
AUDIT_HEALTH_CHECK_MSG = "Audit service is operating normally"

AUDIT_LOGS_ERROR_MSG = "Failed to retrieve audit logs"
AUDIT_STATS_ERROR_MSG = "Failed to retrieve audit statistics"

PROFILE_UPDATE_SUCCESS_MSG = "Profile updated successfully"
PROFILE_GET_SUCCESS_MSG = "Profile retrieved successfully"
PROFILE_STATISTICS_SUCCESS_MSG = "Profile statistics retrieved successfully"
PROFILE_COMPLETION_SUGGESTIONS_SUCCESS_MSG = "Profile completion suggestions retrieved successfully"

FILE_UPLOAD_SUCCESS_MSG = "File uploaded successfully"
FILE_DELETE_SUCCESS_MSG = "File deleted successfully"

PROFILE_SEARCH_FOUND_COUNT_MSG = "Found {count} profiles"

PROFILE_NOT_FOUND_MSG = "User profile not found"
PROFILE_STATISTICS_ERROR_MSG = "Failed to retrieve profile statistics"
PROFILE_SEARCH_ERROR_MSG = "Failed to search profiles"
PROFILE_COMPLETION_SUGGESTIONS_ERROR_MSG = "Failed to retrieve profile completion suggestions"
PROFILE_GET_ERROR_MSG = "Error occurred while retrieving profile"

INTERNAL_ERROR_MSG = "An error occurred, please try again"  