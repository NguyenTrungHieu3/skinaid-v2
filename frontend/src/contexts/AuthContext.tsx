import {
  createContext,
  useState,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import { jwtDecode } from "jwt-decode";
import { getMe } from "../services/authService"; // API /auth/me
// 1. IMPORT THÊM profileService
import { getMyProfile } from "../services/profileService";

// ====== Kiểu dữ liệu người dùng (Giữ nguyên) ======
interface User {
  user_id: string;
  user_name: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_deleted: boolean;
  full_name?: string | null;
  phone?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
  roles?: string[];
  created_at?: string;
}

// ====== Kiểu dữ liệu context (SỬA HÀM LOGIN) ======
interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  // 2. Sửa: 'login' bây giờ nhận 'User' object, không trả về Promise
  login: (token: string, user: User, rememberMe: boolean) => void;
  logout: () => void;
  updateUser: (newUserData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Giữ state loading

  const logout = () => {
    localStorage.removeItem("userToken");
    sessionStorage.removeItem("userToken");
    setUser(null);
    setIsAuthenticated(false);
  };

  // 3. SỬA HÀM FETCHUSER (ĐỂ GỌI CẢ 2 API KHI RELOAD)
  const fetchUser = async (token: string) => {
    try {
      console.log("🔍 [fetchUser] Starting to fetch user data...");

      // Gọi cả 2 API cùng lúc
      const [authResponse, profileResponse] = await Promise.all([
        getMe(token), // (1) Lấy auth data (username, email...) - BẮT BUỘC
        getMyProfile().catch(() => ({ data: { success: false, data: null } })), // (2) Lấy profile data - TÙY CHỌN
      ]);

      console.log("🔍 [fetchUser] API responses:", {
        authSuccess: authResponse.data.success,
        profileSuccess: profileResponse.data.success
      });

      // CHỈ CẦN authResponse thành công là đủ
      if (authResponse.data.success) {
        const authData = authResponse.data.data;

        // Nếu profile API thành công, merge data. Nếu không, chỉ dùng authData
        let fullUser: User = authData;

        if (profileResponse.data.success && profileResponse.data.data) {
          const profileData = profileResponse.data.data;
          fullUser = {
            ...authData,
            ...profileData,
          };
          console.log("✅ [fetchUser] User data merged with profile");
        } else {
          console.log("⚠️ [fetchUser] Profile API failed, using auth data only");
        }

        console.log("✅ [fetchUser] User authenticated successfully", {
          userId: fullUser.user_id,
          roles: fullUser.roles,
          fullUserData: fullUser
        });

        setUser(fullUser);
        setIsAuthenticated(true);
      } else {
        // Chỉ khi auth API fail mới logout
        console.error("❌ [fetchUser] Auth API failed");
        throw new Error("Failed to fetch auth data");
      }
    } catch (error) {
      console.error("❌ [fetchUser] Lỗi khi fetch user data:", error);
      logout();
    }
  };

  // useEffect (Giữ nguyên, nó sẽ gọi 'fetchUser' đã được sửa)
  useEffect(() => {
    const token =
      localStorage.getItem("userToken") || sessionStorage.getItem("userToken");

    const initializeAuth = async () => {
      console.log("🔍 [AuthContext] Initializing auth...", { hasToken: !!token });

      if (token) {
        try {
          const decoded: { exp: number } = jwtDecode(token);
          console.log("🔍 [AuthContext] Token decoded", { exp: decoded.exp, now: Date.now() / 1000 });

          if (decoded.exp * 1000 > Date.now()) {
            console.log("✅ [AuthContext] Token valid, fetching user...");
            await fetchUser(token); // Chờ fetchUser (đã sửa) chạy xong
            console.log("✅ [AuthContext] User fetched successfully");
          } else {
            console.log("❌ [AuthContext] Token expired");
            logout();
          }
        } catch (error) {
          console.error("❌ [AuthContext] Token không hợp lệ:", error);
          logout();
        }
      } else {
        console.log("ℹ️ [AuthContext] No token found");
      }

      console.log("🔍 [AuthContext] Setting isLoading to false");
      setIsLoading(false); // Báo là xong
    };

    initializeAuth();
  }, []); // [] chỉ chạy 1 lần

  // 4. SỬA HÀM LOGIN (ĐỂ NHẬN 'USER' TRỰC TIẾP)
  const login = (token: string, userToSet: User, rememberMe: boolean) => {
    // Lưu token
    if (rememberMe) {
      localStorage.setItem("userToken", token);
    } else {
      sessionStorage.setItem("userToken", token);
    }

    // Dùng 'userToSet' trực tiếp từ LoginForm (đã có full_name)
    // KHÔNG cần gọi 'fetchUser' ở đây nữa
    setUser(userToSet);
    setIsAuthenticated(true);
  };

  // --- HÀM CẬP NHẬT PROFILE (Giữ nguyên) ---
  const updateUser = (newUserData: Partial<User>) => {
    setUser((prevUser) => {
      if (!prevUser) return null;
      return {
        ...prevUser,
        ...newUserData,
      };
    });
  };

  // Giá trị context (Giữ nguyên)
  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    updateUser,
  };

  // Ngăn con render khi đang xác thực lúc reload
  if (isLoading) {
    return <div>Loading SkinAid...</div>; // (Hoặc 1 spinner)
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// ====== Hook (Giữ nguyên) ======
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
