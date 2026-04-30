import axiosClient from '../api/axiosClient';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface NotificationData {
  severity: string;
  wound_type: string;
  analysis_id: string;
}

export interface NotificationItem {
  notification_id: string;
  user_id: string;
  title: string;
  body: string;
  notification_type: string;
  data: NotificationData;
  action_url: string;
  image_url: string | null;
  priority: string;
  severity: string;
  sent_at: string;
  read_at: string | null;
  created_at: string;
  is_read: boolean;
}

export interface NotificationResponse {
  items: NotificationItem[];
  total: number;
  unread_count: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  status_code: number;
}

// ─── API Setup ───────────────────────────────────────────────────────────────────

export const notificationService = {
  /**
   * Lấy danh sách thông báo
   * @param limit Số lượng muốn lấy
   * @param skip Vị trí bắt đầu
   * @param unreadOnly Lấy tin chưa đọc hay lấy tất cả
   */
  async getNotifications(limit = 20, skip = 0, unreadOnly = false): Promise<NotificationResponse> {
    try {
      const { data } = await axiosClient.get<ApiResponse<NotificationResponse>>('/notifications', {
        params: {
          limit,
          skip,
          unread_only: unreadOnly
        }
      });
      return data.data;
    } catch (error) {
      console.error("Failed to fetch notifications API", error);
      throw error;
    }
  },

  /**
   * Đánh dấu 1 thông báo đã đọc
   * @param notificationId id của thông báo
   */
  async markAsRead(notificationId: string): Promise<void> {
    try {
      await axiosClient.patch(`/notifications/${notificationId}/read`);
    } catch (error) {
      console.error(`Failed to mark notification ${notificationId} as read`, error);
    }
  },
  
  /**
   * Đánh dấu toàn bộ đã đọc
   */
  async markAllAsRead(): Promise<void> {
    try {
      await axiosClient.patch('/notifications/read-all');
    } catch (error) {
      console.error("Failed to mark all notifications as read", error);
    }
  }
};
