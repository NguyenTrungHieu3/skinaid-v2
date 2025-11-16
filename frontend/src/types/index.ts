// ====== Kiểu dữ liệu bao bọc (wrapper) mà API backend luôn trả về ======
export interface SuccessResponse<T> {
  success: boolean; // trạng thái xử lý (true/false)
  message: string; // thông điệp mô tả
  data: T; // dữ liệu thực tế (có thể là object, array, string,...)
  timestamp: string; // thời gian trả về
  status_code: number; // mã trạng thái HTTP hoặc mã nội bộ
}

// ====== Kiểu dữ liệu người dùng (User) ======
export interface UserResponse {
  user_id: string;
  user_name: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_deleted: boolean;
  full_name?: string;
  phone?: string;
  gender?: string;
  avatar_url?: string;
  roles?: string[];
}
