import apiClient from "./api";

// 1. Import các kiểu dữ liệu (Types) từ form
// (Giả sử bạn cũng export type từ các form khác)
import type { RegisterFormData } from "../components/auth/RegisterForm";
import type { LoginFormData } from "../components/auth/LoginForm";
import type { ResetPasswordFormData } from "../components/auth/ResetPasswordForm";
import type { SuccessResponse, UserResponse } from "../types/index";

// --- ĐỊNH NGHĨA CÁC KIỂU DỮ LIỆU TRẢ VỀ (DỰA TRÊN API CỦA BẠN) ---

// Kiểu dữ liệu cho data bên trong SuccessResponse (khi đăng nhập)
// Dựa trên schema TokenResponse của backend

interface LoginResponseData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

export type ChangePasswordFormData = {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
};

// Type cho payload gửi đến API (backend)
interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

// --- CÁC HÀM GỌI API ---

/**
 * 1. Đăng ký (Sign Up)
 * Ánh xạ 'username' (FE) sang 'user_name' (BE)
 * Bỏ qua 'gender' vì API /signup chỉ nhận UserCreate (username, email, pass)
 */
export const registerUser = (formData: RegisterFormData) => {
  // Dữ liệu gửi đi phải khớp với schema 'UserCreate' của backend
  const dataToSend = {
    user_name: formData.username, // Ánh xạ tên
    email: formData.email,
    password: formData.password,
    confirm_password: formData.confirmPassword,
    gender: formData.gender,
  };

  // API trả về SuccessResponse chứa UserResponse
  return apiClient.post<SuccessResponse<UserResponse>>(
    "/auth/signup",
    dataToSend
  );
};

/**
 * 2. Đăng nhập (Sign In)
 * (Chúng ta giả định LoginFormData có 'username' và 'password')
 */
export const loginUser = (formData: LoginFormData) => {
  const dataToSend = {
    user_name: formData.username, // Ánh xạ tên
    password: formData.password,
  };

  // API trả về SuccessResponse chứa LoginResponseData (mới)
  return apiClient.post<SuccessResponse<LoginResponseData>>(
    "/auth/signin",
    dataToSend
  );
};

/**
 * 3. Yêu cầu Reset Mật khẩu
 * (API nhận schema PasswordResetRequest)
 */
export const requestPasswordReset = (email: string) => {
  const dataToSend = {
    email: email,
  };
  return apiClient.post<SuccessResponse<{}>>(
    "/auth/password-reset/request",
    dataToSend
  );
};

/**
 * 4. Xác nhận Reset Mật khẩu
 * (API nhận schema PasswordResetConfirm)
 */
export const confirmPasswordReset = (
  formData: ResetPasswordFormData, // Nhận toàn bộ form data
  token: string // và token
) => {
  // Gửi payload đầy đủ mà API yêu cầu
  const dataToSend = {
    email: formData.email,
    token: token,
    new_password: formData.password,
    confirm_password: formData.confirmPassword,
    // (email được backend tự xử lý từ token, không cần gửi)
  };

  return apiClient.post<SuccessResponse<{}>>(
    "/auth/password-reset/confirm",
    dataToSend
  );
};

/**
 * 5. Lấy thông tin User hiện tại (cần token)
 */
export const getMe = (token: string) => {
  return apiClient.get<SuccessResponse<UserResponse>>("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};

/**
 * 6. Đăng xuất (cần token)
 */
export const logoutUser = (token: string) => {
  return apiClient.post<SuccessResponse<{}>>(
    "/auth/logout",
    {}, // API logout không cần body
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
};

/**
 * 7. Thay đổi mật khẩu (khi đã đăng nhập) - (ĐÃ SỬA LỖI)
 */
export const changePassword = (
  formData: ChangePasswordFormData,
  token: string
) => {
  // <-- Thêm 'token'
  const dataToSend: ChangePasswordRequest = {
    old_password: formData.oldPassword,
    new_password: formData.newPassword,
  };

  return apiClient.post<SuccessResponse<{}>>(
    "/auth/change-password",
    dataToSend,
    // Thêm header Authorization
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
};
