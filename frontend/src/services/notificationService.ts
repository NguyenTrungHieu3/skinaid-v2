import apiClient from "./api";

// ---------------------------------------------------------------------------
// TYPES & INTERFACES
// ---------------------------------------------------------------------------

export interface NotificationItem {
  notification_id: string;
  user_id: string | null;
  device_id: string | null;
  title: string;
  body: string;
  notification_type: string;
  data: Record<string, any> | null;
  action_url: string | null;
  image_url: string | null;
  priority: string;
  scheduled_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  status: string;
  failure_reason: string | null;
  retry_count: number;
  max_retries: number;
  provider: string | null;
  provider_message_id: string | null;
  created_at: string;
  updated_at: string;
  is_read: boolean;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface CreateNotificationPayload {
  user_id: string;
  title: string;
  body: string;
  notification_type: string;
  data?: Record<string, any>;
  action_url?: string;
  image_url?: string;
  priority?: string;
}

// ---------------------------------------------------------------------------
// SERVICE FUNCTIONS
// ---------------------------------------------------------------------------

/**
 * Get notifications for the currently authenticated user
 */
export const getNotifications = async (params?: {
  skip?: number;
  limit?: number;
  unread_only?: boolean;
  notification_type?: string;
}): Promise<NotificationListResponse> => {
  const response = await apiClient.get("/notifications", { params });
  const raw = response.data;
  return raw.data || raw;
};

/**
 * Get all notifications in the system (Admin only)
 */
export const getAllNotifications = async (params?: {
  skip?: number;
  limit?: number;
  unread_only?: boolean;
  notification_type?: string;
}): Promise<NotificationListResponse> => {
  const response = await apiClient.get("/notifications/all", { params });
  const raw = response.data;
  return raw.data || raw;
};

/**
 * Get count of unread notifications for current user
 */
export const getUnreadCount = async (): Promise<number> => {
  const response = await apiClient.get("/notifications/unread-count");
  const raw = response.data;
  const payload = raw.data || raw;
  return payload.unread_count ?? 0;
};

/**
 * Mark a single notification as read
 */
export const markAsRead = async (
  notificationId: string
): Promise<NotificationItem> => {
  const response = await apiClient.patch(
    `/notifications/${notificationId}/read`
  );
  const raw = response.data;
  return raw.data || raw;
};

/**
 * Mark all notifications as read
 */
export const markAllRead = async (): Promise<{ updated_count: number }> => {
  const response = await apiClient.patch("/notifications/read-all");
  const raw = response.data;
  return raw.data || raw;
};

/**
 * Delete a single notification
 */
export const deleteNotification = async (
  notificationId: string
): Promise<void> => {
  await apiClient.delete(`/notifications/${notificationId}`);
};

/**
 * Create a notification for a user (admin only)
 */
export const createNotification = async (
  payload: CreateNotificationPayload
): Promise<NotificationItem> => {
  const response = await apiClient.post("/notifications", payload);
  const raw = response.data;
  return raw.data || raw;
};
