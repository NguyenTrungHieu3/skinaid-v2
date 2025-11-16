// --- 1. KIỂU DỮ LIỆU CHUNG ---

// Dữ liệu cơ bản (hiển thị trên Timeline)
export interface HistoryEvent {
  id: string;
  title: string;
  date: string; // ISO Date String
  status: string;
  imageUrl: string;
}

// Dữ liệu chi tiết CỦA MỘT VẾT THƯƠNG
export interface SingleWoundDetail {
  type: string;
  accuracy: number;
  severity: string; // <-- THÊM TRƯỜNG MỚI NÀY
  description: string;
  healingTime: string;
  firstAid: string;
}

// Kiểu dữ liệu gộp (Event và DANH SÁCH chi tiết)
export type CombinedEventDetail = HistoryEvent & {
  detail: SingleWoundDetail[]; // <-- Thay đổi thành một MẢNG
};

// --- 2. DỮ LIỆU MẪU ---

export const DUMMY_EVENTS: HistoryEvent[] = [
  {
    id: "1",
    title: "Phân tích 15/11", // Title chung
    date: "2025-11-15T14:30:00Z",
    status: "2 detections", // Trạng thái chung
    imageUrl: "https://placehold.co/400x300/e0f2f1/009688?text=Wound1",
  },
  {
    id: "2",
    title: "Phân tích 14/11",
    date: "2025-11-14T09:15:00Z",
    status: "1 detection",
    imageUrl: "https://placehold.co/400x300/fff8e1/f39c12?text=Wound2",
  },
  {
    id: "3",
    title: "Phân tích 12/11",
    date: "2025-11-12T17:45:00Z",
    status: "1 detection",
    imageUrl: "https://placehold.co/400x300/e8f5e9/388e3c?text=Wound3",
  },
];

// Dữ liệu chi tiết tương ứng
// Giờ đây mỗi 'id' sẽ trỏ tới một MẢNG các chi tiết
export const DUMMY_DETAILS: { [key: string]: SingleWoundDetail[] } = {
  "1": [
    {
      type: "Trầy xước (Abrasion)",
      accuracy: 92,
      severity: "Nhẹ", // <-- DỮ LIỆU MỚI
      description: "Vết trầy xước nhẹ ở đầu gối, làm sạch và băng bó.",
      healingTime: "5-7 ngày",
      firstAid:
        "1. Rửa sạch vết thương bằng nước mát. 2. Sát trùng nhẹ. 3. Băng lại bằng gạc sạch.",
    },
    {
      type: "Bầm tím (Bruise)",
      accuracy: 85,
      severity: "Nhẹ", // <-- DỮ LIỆU MỚI
      description: "Vết bầm tím nhỏ bên cạnh vết trầy.",
      healingTime: "3-5 ngày",
      firstAid: "Chườm lạnh trong 15 phút đầu tiên để giảm sưng.",
    },
  ],
  "2": [
    {
      type: "Bỏng (Burn)",
      accuracy: 98,
      severity: "Trung bình", // <-- DỮ LIỆU MỚI
      description: "Vết bỏng cấp độ 2 do tiếp xúc với nước sôi.",
      healingTime: "10-14 ngày",
      firstAid:
        "Ngâm vùng bỏng vào nước mát (không phải nước đá) ngay lập tức trong 10-15 phút.",
    },
  ],
  "3": [
    {
      type: "Vết cắt (Laceration)",
      accuracy: 89,
      severity: "Nặng", // <-- DỮ LIỆU MỚI
      description: "Vết cắt nông, không sâu.",
      healingTime: "7 ngày",
      firstAid: "1. Dùng tay ấn nhẹ để cầm máu. 2. Rửa sạch và băng bó.",
    },
  ],
};
