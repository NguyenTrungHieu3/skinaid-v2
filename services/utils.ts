// services/utils.ts

interface ApiError {
  response?: {
    data?: {
      // Project API format: { success: false, message: "..." }
      message?: string;
      // FastAPI validation error format: { detail: [...] | "..." }
      detail?: string | Array<{ msg?: string }>;
    };
  };
  message?: string; // axios network error
}

export const getErrorMessage = (error: ApiError): string => {
  // 1. Project API BE format — { message: "..." }
  const beMessage = error.response?.data?.message;
  if (beMessage && typeof beMessage === 'string') return beMessage;

  // 2. FastAPI validation error format — { detail: "..." | [...] }
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail[0]?.msg || 'Dữ liệu không hợp lệ';
  }

  // 3. axios network error
  if (error.message) return error.message;

  return 'Đã có lỗi kết nối';
};
