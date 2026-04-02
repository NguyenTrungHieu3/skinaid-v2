import axiosClient from "../api/axiosClient";

export const authService = {
  signIn: (data: any) => axiosClient.post("/auth/signin", data),
  signUp: (data: any) => axiosClient.post("/auth/signup", data),
  forgotPassword: (email: string) =>
    axiosClient.post("/auth/password-reset/request", { email }),
  resetPassword: (data: any) =>
    axiosClient.post("/auth/password-reset/confirm", data),
  getMe: () => axiosClient.get("/auth/me"),
  logout: () => axiosClient.post("/auth/logout"),
};
