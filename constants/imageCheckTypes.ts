// constants/imageCheckTypes.ts

export type CheckStatus = "loading" | "fail" | "success";

export interface ImageQualityIssue {
  id: string;
  label: string;
}

// Danh sách lỗi có thể xảy ra
export const QUALITY_ISSUES: Record<string, ImageQualityIssue> = {
  blur: { id: "blur", label: "Ảnh bị mờ" },
  unclear: { id: "unclear", label: "Ảnh không rõ" },
  dark: { id: "dark", label: "Ảnh quá tối" },
  bright: { id: "bright", label: "Ảnh quá sáng" },
  size: { id: "size", label: "Kích thước ảnh không phù hợp" },
  noWound: { id: "noWound", label: "Không phát hiện vết thương" },
};

// Thời gian giả lập AI check (ms)
export const MOCK_CHECK_DURATION = 2500;
