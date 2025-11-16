// --- KIỂU DỮ LIỆU CHO FRONTEND ---

/**
 * Dữ liệu cơ bản cho 1 item trên Timeline
 */
export interface HistoryEvent {
  id: string;
  title: string;
  date: string; // ISO Date String
  status: string;
  imageUrl: string;
}

/**
 * Dữ liệu chi tiết cho 1 vết thương (đã biến đổi)
 */
export interface SingleWoundDetail {
  type: string;
  accuracy: number;
  severity: string;
  description: string;
  healingTime: string;
  firstAid: string; // Đây là chuỗi đã được join (ví dụ: "1. ... 2. ...")
}

/**
 * Kiểu dữ liệu gộp cho trang HistoryDetail
 */
export type CombinedEventDetail = HistoryEvent & {
  detail: SingleWoundDetail[];
};
