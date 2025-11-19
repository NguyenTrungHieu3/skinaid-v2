"""
Messages cho toàn bộ hệ thống
Quy ước: 
- Tất cả messages kết thúc bằng _MSG
- Dynamic messages sử dụng {variable} placeholders
- Nhóm theo module và loại (success/error)
"""

# ============================================
# AUTHENTICATION & AUTHORIZATION (AUTH)
# ============================================

# --- Success Messages ---
USER_REGISTER_SUCCESS_MSG = "Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ."
USER_LOGIN_SUCCESS_MSG = "Đăng nhập thành công"
USER_LOGOUT_SUCCESS_MSG = "Đăng xuất thành công"
PASSWORD_RESET_SUCCESS_MSG = "Mật khẩu đã được cập nhật thành công."
TOKEN_REFRESH_SUCCESS_MSG = "Token refreshed successfully"
AUTH_HEALTH_CHECK_MSG = "Auth service đang hoạt động bình thường"
PASSWORD_RESET_REQUEST_PROCESSING_MSG = "Nếu email tồn tại, một liên kết đặt lại mật khẩu đã được gửi đến địa chỉ email của bạn."
PASSWORD_RESET_PROCESSED_MSG = "Password reset request processed"
PASSWORD_RESET_SUCCESSFUL_MSG = "Password reset successful"
SESSION_TERMINATED_MSG = "Session terminated"
LOGOUT_ALL_DEVICES_SUCCESS_MSG = "Đăng xuất khỏi tất cả thiết bị thành công"
ALL_TOKENS_REVOKED_MSG = "Tất cả token đã bị thu hồi. Vui lòng đăng nhập lại."
PASSWORD_CHANGED_ALL_DEVICES_LOGOUT_MSG = "Mật khẩu đã được thay đổi thành công. Tất cả thiết bị đã được đăng xuất."
PASSWORD_CHANGED_LOGIN_AGAIN_MSG = "Mật khẩu đã được thay đổi. Vui lòng đăng nhập lại trên tất cả thiết bị."
LOGOUT_SUCCESS_TOKENS_REVOKED_MSG = "Đăng xuất thành công. {revoked_count} token đã bị thu hồi."

# --- Error Messages ---
AUTH_INVALID_TOKEN_MSG = "Token không hợp lệ hoặc đã hết hạn"
AUTH_INVALID_TOKEN_TYPE_MSG = "Loại token không hợp lệ"
AUTH_USER_NOT_FOUND_MSG = "Không tìm thấy người dùng"
AUTH_INVALID_REFRESH_TOKEN_MSG = "Refresh token không hợp lệ"
AUTH_RESET_PASSWORD_FAILED_MSG = "Không thể đặt lại mật khẩu"
AUTH_CHANGE_PASSWORD_FAILED_MSG = "Không thể thay đổi mật khẩu"
AUTH_TOKEN_REUSE_DETECTED_MSG = "Phát hiện việc tái sử dụng token"
AUTH_TOKEN_REVOKED_MSG = "Token đã bị thu hồi"

# --- Password Requirements ---
PASSWORD_REQUIREMENTS = [
    "Ít nhất 8 ký tự",
    "Có chữ hoa",
    "Có chữ thường",
    "Có số",
    "Có ký tự đặc biệt"
]



# ============================================
# USER MANAGEMENT (USER)
# ============================================

# --- Error Messages ---
USER_INVALID_DATA_MSG = "Dữ liệu người dùng không hợp lệ"

# ============================================
# AI/ML PROCESSING (AI)
# ============================================

# --- Success Messages ---
AI_ANALYSIS_SUCCESS_MSG = "Phân tích vết thương thành công"
AI_HISTORY_SUCCESS_MSG = "Lấy lịch sử phân tích thành công"
AI_DETAIL_SUCCESS_MSG = "Lấy chi tiết phân tích thành công"
AI_DELETE_SUCCESS_MSG = "Xóa phân tích thành công"

# --- Error Messages ---
AI_MISSING_IDENTIFIER_MSG = "Thiếu thông tin định danh. Vui lòng cung cấp user_id hoặc session_id"
AI_MULTIPLE_IDENTIFIERS_MSG = "Chỉ cung cấp user_id HOẶC session_id, không được cung cấp cả hai"
AI_INVALID_FILE_MSG = "File không hợp lệ. Vui lòng upload ảnh đúng định dạng"
AI_ANALYSIS_NOT_FOUND_MSG = "Không tìm thấy phân tích"
AI_ACCESS_DENIED_MSG = "Bạn không có quyền truy cập phân tích này"
AI_HISTORY_ERROR_MSG = "Không thể lấy lịch sử phân tích"
AI_DETAIL_ERROR_MSG = "Không thể lấy chi tiết phân tích"
AI_DELETE_ERROR_MSG = "Không thể xóa phân tích"


# ============================================
# FIRSTAID GUIDE
# ============================================

# --- Error Messages ---
# --- Success Messages ---
WOUND_TYPES_SUCCESS_MSG = "Lấy danh sách loại vết thương thành công"
FIRSTAID_STATISTICS_SUCCESS_MSG = "Lấy thống kê first aid thành công"

# --- Dynamic Formatted Messages ---
FIRSTAID_GUIDE_FOUND_FOR_MSG = "Lấy hướng dẫn sơ cứu thành công cho {wound_type}/{severity}"
FIRSTAID_GUIDE_NOT_FOUND_FOR_MSG = "Không tìm thấy hướng dẫn sơ cứu cho vết thương loại '{wound_type}' mức độ '{severity}'"
FIRSTAID_GUIDE_NOT_FOUND_WITH_SUBTYPE_MSG = "Không tìm thấy hướng dẫn sơ cứu cho vết thương loại '{wound_type}' mức độ '{severity}' với sub_type '{sub_type}'"
FIRSTAID_GUIDES_FOUND_COUNT_MSG = "Tìm thấy {count} hướng dẫn sơ cứu"
FIRSTAID_GUIDE_AVAILABLE_FOR_MSG = "Hướng dẫn sơ cứu cho {wound_type}/{severity} khả dụng"
FIRSTAID_GUIDE_AVAILABLE_WITH_SUBTYPE_MSG = "Hướng dẫn sơ cứu cho {wound_type}/{severity} với sub_type '{sub_type}' khả dụng"
FIRSTAID_GUIDE_NOT_AVAILABLE_FOR_MSG = "Hướng dẫn sơ cứu cho {wound_type}/{severity} không khả dụng"
FIRSTAID_GUIDE_NOT_AVAILABLE_WITH_SUBTYPE_MSG = "Hướng dẫn sơ cứu cho {wound_type}/{severity} với sub_type '{sub_type}' không khả dụng"

# --- Error Messages ---
FIRSTAID_STATISTICS_ERROR_MSG = "Không thể lấy thống kê first aid"
FIRSTAID_GUIDE_ERROR_MSG = "Không thể lấy hướng dẫn sơ cứu"
WOUND_TYPES_ERROR_MSG = "Không thể lấy loại vết thương"
FIRSTAID_SEARCH_ERROR_MSG = "Không thể tìm kiếm hướng dẫn sơ cứu"
FIRSTAID_VALIDATION_ERROR_MSG = "Không thể kiểm tra tính khả dụng của hướng dẫn"


# ============================================
# AUDIT LOGS (AUDIT)
# ============================================

# --- Success Messages ---
AUDIT_LOGS_SUCCESS_MSG = "Lấy nhật ký kiểm toán thành công"
AUDIT_STATS_SUCCESS_MSG = "Lấy thống kê kiểm toán thành công"
AUDIT_HEALTH_CHECK_MSG = "Audit service đang hoạt động bình thường"

# --- Error Messages ---
AUDIT_LOGS_ERROR_MSG = "Không thể lấy nhật ký kiểm toán"
AUDIT_STATS_ERROR_MSG = "Không thể lấy thống kê kiểm toán"

# ============================================
# USER PROFILE MODULE (PROFILE)
# ============================================

# --- Success Messages ---
PROFILE_UPDATE_SUCCESS_MSG = "Cập nhật profile thành công"
PROFILE_GET_SUCCESS_MSG = "Lấy profile thành công"
PROFILE_STATISTICS_SUCCESS_MSG = "Lấy thống kê profile thành công"
PROFILE_COMPLETION_SUGGESTIONS_SUCCESS_MSG = "Lấy gợi ý hoàn thiện profile thành công"

# --- Dynamic Formatted Messages ---
PROFILE_SEARCH_FOUND_COUNT_MSG = "Tìm thấy {count} profiles"

# --- Error Messages ---
PROFILE_NOT_FOUND_MSG = "Không tìm thấy hồ sơ cá nhân"
PROFILE_STATISTICS_ERROR_MSG = "Không thể lấy thống kê profile"
PROFILE_SEARCH_ERROR_MSG = "Không thể tìm kiếm profiles"
PROFILE_COMPLETION_SUGGESTIONS_ERROR_MSG = "Không thể lấy gợi ý hoàn thiện profile"
PROFILE_GET_ERROR_MSG = "Có lỗi xảy ra khi lấy profile"

# ============================================
# SYSTEM GENERAL (SYSTEM)
# ============================================

# --- Error Messages ---
INTERNAL_ERROR_MSG = "Có lỗi xảy ra, vui lòng thử lại"
