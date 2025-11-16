// src/services/profileService.ts
import apiClient from "./api";
// Giả sử bạn đã định nghĩa SuccessResponse trong file types
import type { SuccessResponse } from "../types/index";

// --- ĐỊNH NGHĨA TYPES (Khớp với Pydantic Schemas mới) ---

// 1. Dữ liệu Backend trả về (GET /profile/me)
// Khớp với pydantic 'UserProfileResponse'
export interface UserProfileResponse {
  user_id: string;
  // Các trường kế thừa từ UserProfileBase
  full_name: string | null;
  phone: string | null;
  date_of_birth: string | null; // (API trả về 'date', ta xử lý 'string')
  gender: string | null;
  address: string | null;
  avatar_url: string | null;
  // Các trường tính toán mới
  age: number | null;
  gender_display: string;
  has_complete_profile: boolean;
  profile_completion_percentage: number;
  created_at: string; // (API trả về 'datetime', ta xử lý 'string')
  updated_at: string;
}

// 2. Dữ liệu Frontend gửi đi (PUT /profile/update)
// Khớp với pydantic 'UserProfileUpdate' (tức là UserProfileBase)
export interface UserProfileUpdate {
  full_name?: string | null;
  phone?: string | null;
  date_of_birth?: string | null; // Frontend sẽ gửi 'dob'
  gender?: string | null;
  address?: string | null;
  avatar_url?: string | null;
  // (Lưu ý: 'email' và các trường y tế KHÔNG có ở đây)
}

// --- HÀM GỌI API ---

/**
 * 1. Lấy thông tin profile chi tiết của user hiện tại
 * (Yêu cầu token, sẽ được 'apiClient' tự động thêm vào nếu bạn cấu hình interceptor)
 */
export const getMyProfile = () => {
  // Kiểu trả về là SuccessResponse chứa UserProfileResponse
  return apiClient.get<SuccessResponse<UserProfileResponse>>("/profile/me");
};

/**
 * 2. Cập nhật thông tin profile của user hiện tại
 * (Yêu cầu token)
 */
export const updateMyProfile = (data: UserProfileUpdate) => {
  // Gửi đi dữ liệu UserProfileUpdate
  // API trả về profile mới (UserProfileResponse)
  return apiClient.put<SuccessResponse<UserProfileResponse>>(
    "/profile/update",
    data
  );
};

// (Bạn có thể thêm hàm upload avatar ở đây sau)
// export const updateAvatar = (formData: FormData) => {
//   return apiClient.post("/profile/avatar-upload", formData, {
//     headers: { "Content-Type": "multipart/form-data" },
//   });
// };
