// constants/types.ts
// ─── Shared TypeScript Interfaces ───────────────────────────────
// Các type dùng chung giữa nhiều file — thay thế `any`.

/**
 * User object trả về từ API /auth/me và /auth/signin.
 */
export interface User {
  id: number;
  user_name: string;
  email: string;
  gender?: string;
  gender_display?: string;
  full_name?: string;
  phone?: string;
  date_of_birth?: string;
  address?: string;
  avatar_url?: string;
  role?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Response wrapper từ FastAPI backend.
 */
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}

/**
 * Auth response từ /auth/signin.
 */
export interface AuthData {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: User;
}

/**
 * Profile data từ /profile/me.
 */
export interface ProfileData {
  full_name?: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
  gender_display?: string;
  address?: string;
  avatar_url?: string;
  created_at?: string;
}

/**
 * Sign-in request payload.
 */
export interface SignInPayload {
  user_name: string;
  password: string;
}

/**
 * Sign-up request payload.
 */
export interface SignUpPayload {
  user_name: string;
  email: string;
  password: string;
  confirm_password: string;
  gender: "Male" | "Female";
}
