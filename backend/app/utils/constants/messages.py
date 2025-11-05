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
USER_REGISTERED_SUCCESS = "Người dùng đăng ký thành công"
USER_REGISTER_SUCCESS_MSG = "Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ."
USER_LOGIN_SUCCESS = "Đăng nhập thành công"
USER_LOGIN_SUCCESS_MSG = "Đăng nhập thành công"
USER_LOGOUT_SUCCESS = "Đăng xuất thành công"
USER_LOGOUT_SUCCESS_MSG = "Đăng xuất thành công"
USER_UPDATED_SUCCESS = "Thông tin người dùng đã được cập nhật thành công"
USER_DELETED_SUCCESS = "Người dùng đã được xóa thành công"
EMAIL_VERIFICATION_SUCCESS_MSG = "Xác thực email thành công"
PASSWORD_RESET_SUCCESS_MSG = "Mật khẩu đã được cập nhật thành công."
PASSWORD_CHANGE_SUCCESS_MSG = "Mật khẩu đã được thay đổi thành công"
TOKEN_REFRESH_SUCCESS_MSG = "Token refreshed successfully"
RESEND_VERIFICATION_SUCCESS_MSG = "Email xác thực đã được gửi lại thành công"
AUTH_HEALTH_CHECK_MSG = "Auth service đang hoạt động bình thường"
PASSWORD_RESET_REQUEST_SUCCESS_MSG = "Nếu email tồn tại, một liên kết đặt lại mật khẩu đã được gửi đến địa chỉ email của bạn."
PASSWORD_RESET_REQUEST_PROCESSING_MSG = "Nếu email tồn tại, một liên kết đặt lại mật khẩu đã được gửi đến địa chỉ email của bạn."
PASSWORD_RESET_PROCESSED_MSG = "Password reset request processed"
PASSWORD_RESET_SUCCESSFUL_MSG = "Password reset successful"
PASSWORD_CHANGED_MSG = "Password changed successfully"
TOKEN_REVOKED_MSG = "Token has been revoked"
SESSION_TERMINATED_MSG = "Session terminated"
EMAIL_VERIFICATION_SENT_MSG = "Email xác thực đã được gửi lại thành công"
VERIFICATION_EMAIL_SENT_MSG = "Verification email sent"

# --- Error Messages ---
AUTH_INVALID_CREDENTIALS_MSG = "Thông tin đăng nhập không hợp lệ"
AUTH_EMAIL_EXISTS_MSG = "Email đã tồn tại trong hệ thống"
AUTH_ACCOUNT_INACTIVE_MSG = "Tài khoản đã bị vô hiệu hóa"
AUTH_PASSWORD_WEAK_MSG = "Mật khẩu không đáp ứng yêu cầu bảo mật"
AUTH_INVALID_TOKEN_MSG = "Token không hợp lệ hoặc đã hết hạn"
AUTH_VERIFICATION_REQUIRED_MSG = "Cần xác thực tài khoản trước khi tiếp tục"
EMAIL_VERIFICATION_FAILED_MSG = "Xác thực email thất bại"
INVALID_TOKEN_TYPE_MSG = "Invalid token type"
INVALID_TOKEN_MSG = "Invalid token"
USER_NOT_FOUND_MSG = "User not found"
INVALID_REFRESH_TOKEN_MSG = "Invalid refresh token"
AUTH_TOKEN_EXPIRED_MSG = "Token đã hết hạn"
AUTH_INVALID_VERIFICATION_TOKEN_MSG = "Token xác thực không hợp lệ"
AUTH_EMAIL_NOT_VERIFIED_MSG = "Email chưa được xác thực"
AUTH_RESEND_VERIFICATION_LIMIT_MSG = "Vượt quá giới hạn gửi lại email xác thực"
AUTH_PASSWORD_RESET_TOKEN_INVALID_MSG = "Token đặt lại mật khẩu không hợp lệ"
AUTH_PASSWORD_RESET_TOKEN_EXPIRED_MSG = "Token đặt lại mật khẩu đã hết hạn"
AUTH_OLD_PASSWORD_INCORRECT_MSG = "Mật khẩu cũ không chính xác"
AUTH_SESSION_EXPIRED_MSG = "Phiên làm việc đã hết hạn"
AUTH_INVALID_TOKEN_TYPE_MSG = "Loại token không hợp lệ"
AUTH_USER_NOT_FOUND_MSG = "Không tìm thấy người dùng"
AUTH_INVALID_REFRESH_TOKEN_MSG = "Refresh token không hợp lệ"
AUTH_RESET_PASSWORD_FAILED_MSG = "Không thể đặt lại mật khẩu"
AUTH_CHANGE_PASSWORD_FAILED_MSG = "Không thể thay đổi mật khẩu"
AUTH_EMAIL_SEND_FAILED_MSG = "Không thể gửi email xác thực"
AUTH_VERIFICATION_FAILED_MSG = "Xác thực email thất bại"
AUTH_VERIFICATION_SYSTEM_ERROR_MSG = "Xác thực email thất bại do lỗi hệ thống"

# --- Password Requirements ---
PASSWORD_REQUIREMENTS = [
    "Ít nhất 8 ký tự",
    "Có chữ hoa",
    "Có chữ thường",
    "Có số",
    "Có ký tự đặc biệt"
]

# --- Email Validation ---
EMAIL_ALREADY_REGISTERED = "Email đã được đăng ký"
INVALID_EMAIL_PASSWORD = "Email hoặc mật khẩu không hợp lệ"
ACCOUNT_DEACTIVATED = "Tài khoản đã bị vô hiệu hóa"
PASSWORD_TOO_WEAK = "Mật khẩu không đáp ứng yêu cầu bảo mật"

# ============================================
# USER MANAGEMENT (USER)
# ============================================

# --- Error Messages ---
USER_NOT_FOUND_MSG = "Không tìm thấy người dùng"
USER_INVALID_DATA_MSG = "Dữ liệu người dùng không hợp lệ"
USER_UPDATE_FAILED_MSG = "Cập nhật thông tin người dùng thất bại"

# ============================================
# FILE OPERATIONS (FILE)
# ============================================

# --- Error Messages ---
FILE_TOO_LARGE_MSG = "Kích thước file vượt quá giới hạn cho phép"
FILE_INVALID_TYPE_MSG = "Loại file không được hỗ trợ"
FILE_UPLOAD_FAILED_MSG = "Tải lên file thất bại"
FILE_CORRUPT_MSG = "File bị hỏng hoặc không thể đọc được"
FILE_SAVE_FAILED_MSG = "Lưu file thất bại"
FILE_EMPTY_MSG = "File trống hoặc không có nội dung"
FILE_UNSAFE_FILENAME_MSG = "Tên file không an toàn"
FILE_INVALID_RESOLUTION_MSG = "Độ phân giải hình ảnh không hợp lệ"

# ============================================
# DATA VALIDATION (VALIDATION)
# ============================================

# --- Error Messages ---
VALIDATION_ERROR_MSG = "Dữ liệu đầu vào không hợp lệ"

# ============================================
# AI/ML PROCESSING (AI)
# ============================================

# --- Success Messages ---
ANALYSIS_SUCCESS_NO_WOUND_MSG = "Phân tích hoàn thành - không phát hiện vết thương"
ANALYSIS_SUCCESS_MSG = "Phân tích hình ảnh thành công"
HEALTH_CHECK_SUCCESS_MSG = "Health check completed"
HISTORY_SUCCESS_MSG = "Lấy lịch sử thành công"
GET_DETAIL_SUCCESS_MSG = "Lấy chi tiết analysis thành công"
DELETE_SUCCESS_MSG = "Xóa analysis thành công"

# --- Error Messages ---
PROCESSING_FAILED_MSG = "Xử lý AI thất bại"
PROCESSING_TIMEOUT_MSG = "Quá thời gian xử lý AI"
AI_MODEL_ERROR_MSG = "Lỗi mô hình AI"
AI_PROCESSING_QUEUE_FULL_MSG = "Hàng đợi xử lý AI đã đầy"
AI_UNSUPPORTED_IMAGE_MSG = "Hình ảnh không được hỗ trợ để xử lý"
AI_LOW_CONFIDENCE_MSG = "Độ tin cậy của kết quả AI quá thấp"
ANALYSIS_NOT_FOUND_MSG = "Không tìm thấy bản phân tích"
HEALTH_CHECK_ERROR_MSG = "Không thể kiểm tra trạng thái AI"
HISTORY_ERROR_MSG = "Không thể lấy lịch sử phân tích"
GET_DETAIL_ERROR_MSG = "Không thể lấy chi tiết phân tích"
DELETE_ERROR_MSG = "Không thể xóa bản phân tích"
AI_ANALYSIS_FAILED_MSG = "AI analysis failed"
ANALYSIS_PROCESS_ERROR_MSG = "Có lỗi xảy ra trong quá trình phân tích"
ANALYSIS_ACCESS_DENIED_MSG = "You can only access your own analyses or all if admin"
GUEST_ACCESS_DENIED_MSG = "Guests can only access guest analyses"
DELETE_ACCESS_DENIED_MSG = "You can only delete your own analyses"
AI_SERVICE_UNAVAILABLE_MSG = "Dịch vụ AI tạm thời không khả dụng, vui lòng thử lại sau"

# ============================================
# RATE LIMITING (RATE)
# ============================================

# --- Error Messages ---
RATE_LIMIT_EXCEEDED_MSG = "Vượt quá giới hạn tốc độ truy cập"
RATE_LIMIT_REGISTRATION_MSG = "Vượt quá giới hạn đăng ký tài khoản"
RATE_LIMIT_UPLOAD_MSG = "Vượt quá giới hạn tải lên file"

# ============================================
# BATCH OPERATIONS (BATCH)
# ============================================

# --- Error Messages ---
BATCH_UPLOAD_FAILED_MSG = "Tải lên hàng loạt thất bại"
BATCH_PARTIAL_SUCCESS_MSG = "Tải lên hàng loạt thành công một phần"
BATCH_SIZE_EXCEEDED_MSG = "Kích thước batch vượt quá giới hạn"

# ============================================
# IMAGE PROCESSING (IMAGE)
# ============================================

# --- Error Messages ---
IMAGE_PREPROCESSING_FAILED_MSG = "Tiền xử lý hình ảnh thất bại"
IMAGE_DUPLICATE_DETECTED_MSG = "Phát hiện hình ảnh trùng lặp"
IMAGE_METADATA_EXTRACTION_FAILED_MSG = "Trích xuất metadata hình ảnh thất bại"

# ============================================
# RBAC (ROLE-BASED ACCESS CONTROL)
# ============================================

# --- Error Messages ---
ROLE_NOT_FOUND_MSG = "Không tìm thấy vai trò"
PERMISSION_NOT_FOUND_MSG = "Không tìm thấy quyền hạn"
ROLE_ASSIGNMENT_FAILED_MSG = "Phân công vai trò thất bại"
PERMISSION_DENIED_MSG = "Không có quyền truy cập"
INSUFFICIENT_PERMISSIONS_MSG = "Quyền hạn không đủ"

# ============================================
# DATABASE OPERATIONS (DATABASE)
# ============================================

# --- Error Messages ---
DATABASE_CONNECTION_ERROR_MSG = "Không thể kết nối đến cơ sở dữ liệu"
DATABASE_QUERY_ERROR_MSG = "Lỗi thực hiện truy vấn cơ sở dữ liệu"
DATABASE_TRANSACTION_ERROR_MSG = "Lỗi giao dịch cơ sở dữ liệu"
DATABASE_CONNECTION_TIMEOUT_MSG = "Quá thời gian kết nối cơ sở dữ liệu"
DATABASE_LOCK_ERROR_MSG = "Lỗi khóa cơ sở dữ liệu"

# ============================================
# EMAIL SERVICES (EMAIL)
# ============================================

# --- Error Messages ---
EMAIL_SEND_FAILED_MSG = "Gửi email thất bại"
EMAIL_INVALID_FORMAT_MSG = "Định dạng email không hợp lệ"
EMAIL_SMTP_ERROR_MSG = "Lỗi kết nối SMTP"
EMAIL_TEMPLATE_ERROR_MSG = "Lỗi mẫu email"
EMAIL_RATE_LIMIT_EXCEEDED_MSG = "Vượt quá giới hạn gửi email"

# ============================================
# FIRST AID MODULE (FIRSTAID)
# ============================================

# --- Success Messages ---
FIRSTAID_GUIDE_SUCCESS_MSG = "Lấy hướng dẫn sơ cứu thành công"
WOUND_TYPES_SUCCESS_MSG = "Lấy danh sách loại vết thương thành công"
FIRSTAID_SEARCH_SUCCESS_MSG = "Tìm thấy hướng dẫn sơ cứu"
FIRSTAID_STATISTICS_SUCCESS_MSG = "Lấy thống kê first aid thành công"
FIRSTAID_VALIDATION_AVAILABLE_MSG = "Hướng dẫn sơ cứu khả dụng"
FIRSTAID_VALIDATION_NOT_AVAILABLE_MSG = "Hướng dẫn sơ cứu không khả dụng"

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
FIRSTAID_GUIDE_NOT_FOUND_MSG = "Không tìm thấy hướng dẫn sơ cứu"
FIRSTAID_INVALID_WOUND_TYPE_MSG = "Loại vết thương không hợp lệ"
FIRSTAID_INVALID_SEVERITY_MSG = "Mức độ nghiêm trọng không hợp lệ"
FIRSTAID_GUIDE_CREATE_FAILED_MSG = "Tạo hướng dẫn sơ cứu thất bại"
FIRSTAID_GUIDE_UPDATE_FAILED_MSG = "Cập nhật hướng dẫn sơ cứu thất bại"
FIRSTAID_GUIDE_DELETE_FAILED_MSG = "Xóa hướng dẫn sơ cứu thất bại"
FIRSTAID_SEARCH_FAILED_MSG = "Tìm kiếm hướng dẫn sơ cứu thất bại"
FIRSTAID_STATISTICS_ERROR_MSG = "Không thể lấy thống kê first aid"
FIRSTAID_GUIDE_ERROR_MSG = "Không thể lấy hướng dẫn sơ cứu"
WOUND_TYPES_ERROR_MSG = "Không thể lấy loại vết thương"
FIRSTAID_SEARCH_ERROR_MSG = "Không thể tìm kiếm hướng dẫn sơ cứu"
FIRSTAID_VALIDATION_ERROR_MSG = "Không thể kiểm tra tính khả dụng của hướng dẫn"

# ============================================
# GUEST SESSION MODULE (GUEST)
# ============================================

# --- Success Messages ---
GUEST_SESSION_CREATE_SUCCESS_MSG = "Tạo guest session thành công"
GUEST_SESSION_GET_SUCCESS_MSG = "Lấy guest session thành công"
GUEST_UPLOAD_CREATE_SUCCESS_MSG = "Upload file thành công"
GUEST_ANALYSIS_CREATE_SUCCESS_MSG = "Phân tích thành công"
GUEST_UPLOADS_GET_SUCCESS_MSG = "Lấy uploads thành công"
GUEST_ANALYSES_GET_SUCCESS_MSG = "Lấy analyses thành công"
GUEST_STATISTICS_SUCCESS_MSG = "Lấy thống kê guest thành công"

# --- Dynamic Formatted Messages ---
GUEST_UPLOADS_FOUND_COUNT_MSG = "Lấy {count} uploads thành công"
GUEST_ANALYSES_FOUND_COUNT_MSG = "Lấy {count} analyses thành công"

# --- Error Messages ---
GUEST_SESSION_NOT_FOUND_MSG = "Không tìm thấy phiên làm việc khách"
GUEST_SESSION_EXPIRED_MSG = "Phiên làm việc khách đã hết hạn"
GUEST_SESSION_CREATE_ERROR_MSG = "Không thể tạo guest session"
GUEST_SESSION_ERROR_MSG = "Không thể tạo guest session"
GUEST_UPLOAD_LIMIT_EXCEEDED_MSG = "Vượt quá giới hạn tải lên của khách"
GUEST_ANALYSIS_LIMIT_EXCEEDED_MSG = "Vượt quá giới hạn phân tích của khách"
GUEST_UPLOAD_CREATE_ERROR_MSG = "Không thể tạo guest upload"
GUEST_ANALYSIS_CREATE_ERROR_MSG = "Không thể tạo guest analysis"
GUEST_STATISTICS_ERROR_MSG = "Không thể lấy thống kê guest"
GUEST_INVALID_SESSION_ID_MSG = "ID phiên làm việc khách không hợp lệ"
GUEST_UPLOAD_ERROR_MSG = "Không thể upload file"
GUEST_UPLOADS_ERROR_MSG = "Không thể lấy danh sách uploads"
GUEST_ANALYSES_ERROR_MSG = "Không thể lấy danh sách analyses"
GUEST_SESSION_NOT_EXISTS_MSG = "Guest session không tồn tại"
GUEST_SESSION_GET_ERROR_MSG = "Không thể lấy guest session"
GUEST_ANALYSIS_ERROR_MSG = "Không thể phân tích"

# ============================================
# USER PROFILE MODULE (PROFILE)
# ============================================

# --- Success Messages ---
PROFILE_UPDATE_SUCCESS_MSG = "Cập nhật profile thành công"
PROFILE_GET_SUCCESS_MSG = "Lấy profile thành công"
PROFILE_STATISTICS_SUCCESS_MSG = "Lấy thống kê profile thành công"
PROFILE_SEARCH_SUCCESS_MSG = "Tìm thấy profiles"
PROFILE_COMPLETION_SUGGESTIONS_SUCCESS_MSG = "Lấy gợi ý hoàn thiện profile thành công"

# --- Dynamic Formatted Messages ---
PROFILE_SEARCH_FOUND_COUNT_MSG = "Tìm thấy {count} profiles"

# --- Error Messages ---
PROFILE_NOT_FOUND_MSG = "Không tìm thấy hồ sơ cá nhân"
PROFILE_UPDATE_FAILED_MSG = "Cập nhật hồ sơ cá nhân thất bại"
PROFILE_INVALID_DATA_MSG = "Dữ liệu hồ sơ cá nhân không hợp lệ"
PROFILE_AVATAR_UPLOAD_FAILED_MSG = "Tải lên ảnh đại diện thất bại"
PROFILE_STATISTICS_ERROR_MSG = "Không thể lấy thống kê profile"
PROFILE_SEARCH_ERROR_MSG = "Không thể tìm kiếm profiles"
PROFILE_COMPLETION_SUGGESTIONS_ERROR_MSG = "Không thể lấy gợi ý hoàn thiện profile"
PROFILE_GET_ERROR_MSG = "Có lỗi xảy ra khi lấy profile"

# ============================================
# UPLOAD MANAGEMENT (UPLOAD)
# ============================================

# --- Success Messages ---
UPLOAD_LOGS_GET_SUCCESS_MSG = "Lấy lịch sử upload thành công"
UPLOAD_LOG_CREATE_SUCCESS_MSG = "Tạo upload log thành công"
UPLOAD_LOG_UPDATE_SUCCESS_MSG = "Cập nhật trạng thái upload log thành công"
UPLOAD_STATISTICS_SUCCESS_MSG = "Lấy thống kê upload thành công"

# --- Dynamic Formatted Messages ---
UPLOAD_LOGS_FOUND_COUNT_MSG = "Lấy {count} lịch sử upload thành công"

# --- Error Messages ---
UPLOAD_LOGS_RETRIEVAL_FAILED_MSG = "Không thể lấy lịch sử upload"
UPLOAD_LOGS_UNEXPECTED_ERROR_MSG = "Có lỗi không mong muốn xảy ra khi lấy lịch sử upload"
UPLOAD_LOG_CREATE_ERROR_MSG = "Không thể tạo upload log"
UPLOAD_LOG_UPDATE_ERROR_MSG = "Không thể cập nhật upload log"
UPLOAD_LOG_NOT_FOUND_MSG = "Không tìm thấy upload log"
UPLOAD_STATISTICS_ERROR_MSG = "Không thể lấy thống kê upload"

# ============================================
# SYSTEM GENERAL (SYSTEM)
# ============================================

# --- Error Messages ---
INTERNAL_ERROR_MSG = "Có lỗi xảy ra, vui lòng thử lại"
SYSTEM_ERROR_MSG = "Lỗi hệ thống, vui lòng thử lại sau"
PASSWORD_RESET_ERROR_MSG = "Không thể đặt lại mật khẩu"
PASSWORD_CHANGE_ERROR_MSG = "Không thể thay đổi mật khẩu"