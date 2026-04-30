// constants/imageCheckTypes.ts

export type CheckStatus = "loading" | "fail" | "success";

export interface ImageQualityIssue {
  id: string;
  label: string;
  description: string;   // Giải thích chi tiết cho user
  autoFixable: boolean;  // Có thể tự động sửa phía client không
}

// Danh sách lỗi chất lượng ảnh
export const QUALITY_ISSUES: Record<string, ImageQualityIssue> = {
  blur: {
    id: "blur",
    label: "Ảnh bị mờ",
    description: "Ảnh thiếu chi tiết sắc nét. Hãy giữ tay cố định khi chụp hoặc dùng nút cắt ảnh.",
    autoFixable: true,
  },
  unclear: {
    id: "unclear",
    label: "Ảnh không rõ",
    description: "Không thể đọc thông tin từ ảnh. Vui lòng chụp lại trong điều kiện sáng hơn.",
    autoFixable: false,
  },
  dark: {
    id: "dark",
    label: "Ảnh quá tối",
    description: "Độ sáng không đủ. Hãy chụp ảnh nơi có nhiều ánh sáng tự nhiên.",
    autoFixable: false,
  },
  bright: {
    id: "bright",
    label: "Ảnh quá sáng",
    description: "Ảnh bị cháy sáng. Tránh chụp ngược sáng hoặc dưới đèn flash mạnh.",
    autoFixable: false,
  },
  size: {
    id: "size",
    label: "Ảnh quá nhỏ",
    description: "Ảnh cần ít nhất 300×300 px để AI phân tích chính xác.",
    autoFixable: true,
  },
  noWound: {
    id: "noWound",
    label: "Không phát hiện vết thương",
    description: "Hãy đảm bảo vết thương nằm rõ ràng ở trung tâm khung hình.",
    autoFixable: false,
  },
  aspect: {
    id: "aspect",
    label: "Tỉ lệ ảnh bất thường",
    description: "Ảnh quá dài hoặc quá rộng (> 4:1). Sẽ tự động crop về tỉ lệ chuẩn.",
    autoFixable: true,
  },
  tooSmall: {
    id: "tooSmall",
    label: "File ảnh quá nhỏ",
    description: "File ảnh nhỏ hơn 20KB, có thể chất lượng rất thấp. Chụp lại để có kết quả tốt hơn.",
    autoFixable: false,
  },
  tooLarge: {
    id: "tooLarge",
    label: "File ảnh quá lớn",
    description: "File ảnh lớn hơn 20MB. Sẽ tự động nén lại trước khi phân tích.",
    autoFixable: true,
  },
};

// Thời gian check thực tế (ms) — để hiển thị animation tối thiểu
export const MIN_CHECK_DURATION = 1500;
