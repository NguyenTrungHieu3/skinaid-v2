import apiClient from "./api";
import type { SuccessResponse } from "../types";

// Guest Session Response từ backend
export interface GuestSessionResponse {
  session_id: string;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  ip_address: string | null;
  user_agent: string | null;
  upload_count: number;
  analysis_count: number;
}

/**
 * Tạo guest session mới
 * Backend sẽ trả về session_id để sử dụng cho các requests tiếp theo
 */
export const createGuestSession = async (): Promise<GuestSessionResponse> => {
  const response = await apiClient.post<SuccessResponse<GuestSessionResponse>>(
    "/guest/session"
  );
  return response.data.data;
};

/**
 * Lấy thông tin guest session theo ID
 */
export const getGuestSession = async (
  sessionId: string
): Promise<GuestSessionResponse> => {
  const response = await apiClient.get<SuccessResponse<GuestSessionResponse>>(
    `/guest/session/${sessionId}`
  );
  return response.data.data;
};
