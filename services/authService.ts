import axiosClient from "../api/axiosClient";

export const authService = {
  // FastAPI thường dùng "username" nhưng nếu bạn chắc chắn Swagger là "user_name" thì giữ nguyên
  signIn: (data: any) => axiosClient.post("/auth/signin", data),

  signUp: (data: any) => axiosClient.post("/auth/signup", data),

  forgotPassword: (email: string) =>
    axiosClient.post("/auth/password-reset/request", { email }),

  resetPassword: (data: any) =>
    axiosClient.post("/auth/password-reset/confirm", data),

  getMe: (token: string) =>
    axiosClient.get("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    }),

  refreshToken: (refresh_token: string) =>
    axiosClient.post("/auth/refresh", { refresh_token }),

  logout: () => axiosClient.post("/auth/logout"),

  changePassword: (data: {
    old_password: string;
    new_password: string;
    confirm_password: string;
  }) => axiosClient.post("/auth/change-password", data),

  getProfile: () => axiosClient.get("/profile/me"),

  updateProfile: (data: {
    full_name?: string;
    phone?: string;
    date_of_birth?: string;
    gender?: string;
    address?: string;
  }) => axiosClient.put("/profile/update", data),

  uploadAvatar: (formData: FormData) =>
    axiosClient.post("/profile/avatar-upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};
