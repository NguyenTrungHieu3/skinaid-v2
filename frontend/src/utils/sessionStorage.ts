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
  const expiryDate = new Date(expiryStr);
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
