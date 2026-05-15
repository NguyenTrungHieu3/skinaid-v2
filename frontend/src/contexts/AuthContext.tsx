import {
  createContext,
  useState,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import apiClient from "../services/api";
import { getMe, logoutUser } from "../services/authService"; // API /auth/me
import { abortActiveAnalysis } from "../services/aiService";
// 1. IMPORT THÊM profileService
import { getMyProfile } from "../services/profileService";
import { useTranslation } from "react-i18next";

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
  login: (token: string, refreshToken: string, user: User, rememberMe: boolean) => void;
  logout: () => void;
  updateUser: (newUserData: Partial<User>) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Giữ state loading

  const { t } = useTranslation();
  // 1. STATE MỚI: Quản lý thông báo hết phiên
  const [isSessionExpired, setIsSessionExpired] = useState(false);

  // --- HÀM LOGOUT CHÍNH THỨC ---
  // Hàm này sẽ xóa data và redirect
  const performLogout = () => {
    // Abort any in-flight wound analysis (TC-LO-09)
    abortActiveAnalysis();
    localStorage.removeItem("userToken");
    localStorage.removeItem("refreshToken");
    sessionStorage.removeItem("userToken");
    sessionStorage.removeItem("refreshToken");
    setUser(null);
    setIsAuthenticated(false);
    setIsSessionExpired(false); // Tắt modal sau khi logout
    window.location.href = "/login"; // Chuyển hướng
  };

  // --- HÀM GỌI API LOGOUT (Do người dùng chủ động bấm) ---
  const logout = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.warn("Logout error:", error);
    } finally {
      performLogout();
    }
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
        profileSuccess: profileResponse.data.success,
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
          console.log(
            "⚠️ [fetchUser] Profile API failed, using auth data only"
          );
        }

        console.log("✅ [fetchUser] User authenticated successfully", {
          userId: fullUser.user_id,
          roles: fullUser.roles,
          fullUserData: fullUser,
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
      performLogout();
    }
  };

  // 2. THÊM HÀM refreshUser: Hàm này public ra ngoài để các component khác gọi
  const refreshUser = async () => {
    const token =
      localStorage.getItem("userToken") || sessionStorage.getItem("userToken");
    if (token) {
      await fetchUser(token); // Tái sử dụng logic fetchUser ở trên
    }
  };

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token =
          localStorage.getItem("userToken") || sessionStorage.getItem("userToken");
        const refreshToken =
          localStorage.getItem("refreshToken") || sessionStorage.getItem("refreshToken");

        if (!token && !refreshToken) {
          // No credentials at all — stay logged out
          return;
        }

        if (token) {
          // fetchUser calls /auth/me via apiClient.
          // The request interceptor in api.ts will proactively refresh
          // the access token if it is expired before the request fires.
          console.log("ℹ️ [AuthContext] Initialising session, fetching user...");
          await fetchUser(token);
        }
      } catch (error) {
        console.error("❌ [AuthContext] initializeAuth failed:", error);
        performLogout();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  // Cross-tab session sync (TC-LO-05): detect logout from other tabs
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === "userToken" && e.newValue === null && e.oldValue) {
        // Token cleared on another tab -> force logout here too
        setUser(null);
        setIsAuthenticated(false);
        setIsSessionExpired(false);
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  // 4. SỬA HÀM LOGIN (ĐỂ NHẬN 'USER' TRỰC TIẾP VÀ REFRESH TOKEN)
  const login = (token: string, refreshToken: string, userToSet: User, rememberMe: boolean) => {
    // Lưu token
    if (rememberMe) {
      localStorage.setItem("userToken", token);
      localStorage.setItem("refreshToken", refreshToken);
    } else {
      sessionStorage.setItem("userToken", token);
      sessionStorage.setItem("refreshToken", refreshToken);
    }

    // Dùng 'userToSet' trực tiếp từ LoginForm (đã có full_name)
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
    refreshUser,
  };

  // Ngăn con render khi đang xác thực lúc reload
  if (isLoading) {
    return (
      <div className="full-screen-loading">
        <div className="loading-spinner"></div>
        <div className="loading-text">{t("auth_page.loading")}</div>

        {/* Tùy chọn: Nếu muốn hiện logo thay vì text thì dùng dòng dưới */}
        {/* <img src="/path/to/logo.png" alt="Logo" style={{ width: '60px', marginTop: '10px' }} /> */}
      </div>
    );
  }

  // 3. RENDER GIAO DIỆN + MODAL
  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout,
        updateUser,
        refreshUser,
      }}
    >
      {/* Hiển thị children (App) */}
      {!isLoading && children}

      {/* Loading Screen */}
      {isLoading && <div>{t("auth_page.loading")}</div>}

      {/* 4. MODAL HẾT PHIÊN ĐĂNG NHẬP */}
      {isSessionExpired && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
          }}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "2rem",
              borderRadius: "8px",
              textAlign: "center",
              maxWidth: "400px",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}
          >
            <h3 style={{ marginTop: 0, color: "#d32f2f" }}>
              {t("auth_page.session_expired.title")}
            </h3>
            <p>{t("auth_page.session_expired.message")}</p>
            <button
              onClick={performLogout}
              style={{
                backgroundColor: "#009688",
                color: "white",
                border: "none",
                padding: "10px 20px",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "1rem",
                fontWeight: "bold",
              }}
            >
              {t("auth_page.session_expired.button")}
            </button>
          </div>
        </div>
      )}
    </AuthContext.Provider>
  );
};

// ====== Hook (Giữ nguyên) ======
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
