/**
 * Kiểu response chung cho API khi thành công.
 * T: là kiểu của 'data' (ví dụ: User, WoundAnalysisResponse)
 */
export interface ApiSuccessResponse<T> {
  status: "success";
  data: T;
  message?: string;
}

/**
 * Kiểu response chung cho API khi thất bại.
 */
export interface ApiErrorResponse {
  status: "error";
  message: string;
  detail?: any;
}
