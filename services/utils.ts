// services/utils.ts
export const getErrorMessage = (error: any) => {
  const detail = error.response?.data?.detail;
  if (!detail) return "Đã có lỗi kết nối";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail[0]?.msg || "Dữ liệu không hợp lệ";
  return "Lỗi không xác định";
};
