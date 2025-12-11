import { useState, useEffect } from "react";
import { createGuestSession } from "../services/guestService";
import {
  getSessionId,
  saveSessionId,
  clearSessionId,
  hasValidSession,
} from "../utils/sessionStorage";

/**
 * Hook để quản lý guest session
 * Tự động tạo session nếu user chưa đăng nhập và chưa có session
 */
export const useGuestSession = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  // Bắt đầu với isLoading = true để đảm bảo caller đợi session sẵn sàng
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Kiểm tra xem user đã đăng nhập chưa
  const isAuthenticated = (): boolean => {
    const token =
      localStorage.getItem("userToken") ||
      sessionStorage.getItem("userToken");
    return !!token;
  };

  // Khởi tạo session khi component mount
  useEffect(() => {
    const initializeSession = async () => {
      // Nếu đã đăng nhập, không cần guest session
      if (isAuthenticated()) {
        setSessionId(null);
        setIsLoading(false);
        return;
      }

      // Kiểm tra có session hợp lệ không
      const existingSession = getSessionId();
      if (existingSession) {
        setSessionId(existingSession);
        setIsLoading(false);
        return;
      }

      // Tạo session mới - giữ isLoading = true
      setError(null);

      try {
        console.log("[useGuestSession] Calling createGuestSession API...");
        const session = await createGuestSession();
        console.log("[useGuestSession] API Response:", session);
        console.log("[useGuestSession] session_id:", session.session_id);
        console.log("[useGuestSession] expires_at:", session.expires_at);

        saveSessionId(session.session_id, session.expires_at);
        console.log("[useGuestSession] Session saved to localStorage!");
        console.log("[useGuestSession] Verify localStorage:", localStorage.getItem("guest_session_id"));

        setSessionId(session.session_id);
      } catch (err) {
        setError("Không thể tạo guest session");
        console.error("[useGuestSession] Error creating session:", err);
      } finally {
        setIsLoading(false);
        console.log("[useGuestSession] isLoading set to false");
      }
    };

    initializeSession();
  }, []);

  // Xóa session (ví dụ khi user đăng nhập)
  const clearSession = () => {
    clearSessionId();
    setSessionId(null);
  };

  // Refresh session manually
  const refreshSession = async () => {
    if (isAuthenticated()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const session = await createGuestSession();
      saveSessionId(session.session_id, session.expires_at);
      setSessionId(session.session_id);
    } catch (err) {
      setError("Không thể refresh guest session");
      console.error("Error refreshing guest session:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    sessionId,
    isLoading,
    error,
    hasValidSession: hasValidSession(),
    clearSession,
    refreshSession,
  };
};
