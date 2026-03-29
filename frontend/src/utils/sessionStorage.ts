/**
 * Utility để quản lý guest session_id trong localStorage
 */

const SESSION_KEY = "guest_session_id";
const SESSION_EXPIRY_KEY = "guest_session_expiry";

/**
 * Lưu session_id vào localStorage
 */
export const saveSessionId = (sessionId: string, expiresAt: string): void => {
  localStorage.setItem(SESSION_KEY, sessionId);
  localStorage.setItem(SESSION_EXPIRY_KEY, expiresAt);
};

/**
 * Lấy session_id từ localStorage (nếu chưa hết hạn)
 */
export const getSessionId = (): string | null => {
  const sessionId = localStorage.getItem(SESSION_KEY);
  const expiryStr = localStorage.getItem(SESSION_EXPIRY_KEY);

  if (!sessionId || !expiryStr) {
    return null;
  }

  // Kiểm tra xem session đã hết hạn chưa
  // Backend trả về expires_at dạng UTC nhưng không có "Z" suffix
  // Cần thêm "Z" để JavaScript parse đúng là UTC time
  let expiryDate: Date;

  // Check if string already has timezone info:
  // - Ends with "Z" (UTC)
  // - Contains "+" after "T" (positive offset like +07:00)
  // - Contains "-" after the time part (negative offset like -05:00)
  const hasTimezoneInfo =
    expiryStr.endsWith("Z") ||
    (expiryStr.includes("T") && expiryStr.split("T")[1]?.includes("+")) ||
    (expiryStr.includes("T") && expiryStr.split("T")[1]?.match(/-\d{2}:/));

  if (hasTimezoneInfo) {
    // Already has timezone info
    expiryDate = new Date(expiryStr);
  } else {
    // No timezone info - assume UTC and append "Z"
    expiryDate = new Date(expiryStr + "Z");
  }

  const now = new Date();

  if (now >= expiryDate) {
    // Session đã hết hạn, xóa đi
    clearSessionId();
    return null;
  }

  return sessionId;
};

/**
 * Xóa session_id khỏi localStorage
 */
export const clearSessionId = (): void => {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(SESSION_EXPIRY_KEY);
};

/**
 * Kiểm tra có session_id hợp lệ không
 */
export const hasValidSession = (): boolean => {
  return getSessionId() !== null;
};
