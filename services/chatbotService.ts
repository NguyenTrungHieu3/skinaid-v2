// services/chatbotService.ts
// Chatbot API — Session-based (v2)
// Mode 1: App Guide (analysis_id = null → Redis, TTL 24h)
// Mode 2: Wound Advisor (analysis_id = UUID → PostgreSQL, persistent)

import axiosClient from "../api/axiosClient";

// ── Timeout riêng cho chatbot (AI inference có thể chậm) ────────
const CHATBOT_TIMEOUT = 60_000; // 60 giây

// ── Request types ───────────────────────────────────────────────

export interface CreateSessionRequest {
  analysis_id?: string | null;
}

export interface SendMessageRequest {
  message: string;
}

// ── Response types ──────────────────────────────────────────────

export interface SessionData {
  session_id: string;
  analysis_id: string | null;
  session_type: string; // "app_guide" | "wound_advisor"
  max_messages: number;
  created_at: string;
}

export interface SessionListItem {
  session_id: string;
  analysis_id: string | null;
  session_type: string;
  message_count: number;
  last_message_at: string;
  status: string;
  created_at: string;
}

export interface MessageReplyData {
  reply: string;
  session_id: string;
  tokens_used: number;
  message_count: number;
  remaining_messages: number;
  created_at: string;
}

export interface SessionDetailData {
  session_id: string;
  analysis_id: string | null;
  session_type: string;
  messages: Array<{
    role: string;
    content: string;
    created_at: string;
  }>;
  message_count: number;
  remaining_messages: number;
  status: string;
  created_at: string;
}

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  status_code: number;
}

// ── Service ─────────────────────────────────────────────────────

export const chatbotService = {
  /**
   * Tạo phiên chat mới.
   * - Không truyền analysis_id → App Guide (Redis, TTL 24h)
   * - Truyền analysis_id → Wound Advisor (PostgreSQL, persistent)
   */
  createSession: (analysisId?: string | null) =>
    axiosClient.post<ApiResponse<SessionData>>(
      "/chatbot/sessions",
      analysisId ? { analysis_id: analysisId } : {}
    ),

  /**
   * Gửi tin nhắn trong phiên chat.
   * AI trả lời dựa trên mode (App Guide / Wound Advisor).
   * Timeout: 60s (AI inference có thể chậm).
   */
  sendMessage: (sessionId: string, message: string) =>
    axiosClient.post<ApiResponse<MessageReplyData>>(
      `/chatbot/sessions/${sessionId}/messages`,
      { message },
      { timeout: CHATBOT_TIMEOUT }
    ),

  /**
   * Lấy chi tiết phiên chat (bao gồm messages).
   */
  getSession: (sessionId: string) =>
    axiosClient.get<ApiResponse<SessionDetailData>>(
      `/chatbot/sessions/${sessionId}`
    ),

  /**
   * Lấy danh sách tất cả phiên chat của user.
   * (Dùng cho luồng 2 — lịch sử chat)
   */
  getSessions: () =>
    axiosClient.get<ApiResponse<SessionListItem[]>>("/chatbot/sessions"),

  /**
   * Xóa phiên chat.
   * (Dùng cho luồng 2 — quản lý lịch sử)
   */
  deleteSession: (sessionId: string) =>
    axiosClient.delete<ApiResponse<string>>(
      `/chatbot/sessions/${sessionId}`
    ),
};
