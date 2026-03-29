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
  sub_type:string;
  healingTime: string;
  firstAid: string; // Đây là chuỗi đã được join (ví dụ: "1. ... 2. ...")
  shouldDo: string; // Mô tả các bước nên làm
  shouldNotDo: string; // Mô tả các bước không nên làm
  titleGuide:string; // Tiêu đề hướng dẫn sơ cứu
  suppliesNeeded: string; // Vật tư cần thiết
  reliable_source: Record<string, any>; 
}

/**
 * Kiểu dữ liệu gộp cho trang HistoryDetail
 */
export type CombinedEventDetail = HistoryEvent & {
  detail: SingleWoundDetail[];
};
