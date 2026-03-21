import axios from "axios";
import { jwtDecode } from "jwt-decode";
// import { v4 as uuidv4 } from "uuid";

// Hàm lấy hoặc tạo session ID cho khách
// const getGuestSessionId = () => {
//   let sessionId = localStorage.getItem("guest_session_id");
//   if (!sessionId) {
//     sessionId = uuidv4();
//     localStorage.setItem("guest_session_id", sessionId);
//   }
//   return sessionId;
// };

// Lấy API URL từ environment variable hoặc dùng mặc định
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// Export BACKEND_URL để dùng cho static files (images, uploads)
// Ví dụ: VITE_BACKEND_URL = "http://18.179.57.221:8000" (no /api/v1 suffix)
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

// Tạo 1 instance của axios với cấu hình mặc định
const apiClient = axios.create({
  baseURL: API_BASE_URL,

  // KHÔNG set "Content-Type" mặc định ở đây
});

// apiClient.interceptors.request.use((config) => {
//   const token = localStorage.getItem("userToken");

//   // 1. Nếu có Token User (Đăng nhập)
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }

//   // 2. Luôn gửi kèm Session ID cho trường hợp là Khách hoặc Token lỗi
//   // Backend sẽ đọc header: X-Session-ID
//   config.headers["X-Session-ID"] = getGuestSessionId();

//   return config;
// });

// export default apiClient;

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Helper: check if a JWT is expired (or will expire within a small buffer)
const isTokenExpired = (token: string, bufferSeconds = 10): boolean => {
  try {
    const { exp } = jwtDecode<{ exp: number }>(token);
    return exp * 1000 < Date.now() + bufferSeconds * 1000;
  } catch {
    return true; // treat undecodable tokens as expired
  }
};

// Helper: perform a token refresh and persist the new tokens.
// Returns the new access token, or null on failure.
const doRefresh = async (): Promise<string | null> => {
  const refreshToken =
    localStorage.getItem("refreshToken") ||
    sessionStorage.getItem("refreshToken");

  if (!refreshToken) return null;

  try {
    const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });

    const newAccessToken: string = data.data.access_token;
    const newRefreshToken: string = data.data.refresh_token;

    if (localStorage.getItem("refreshToken")) {
      localStorage.setItem("userToken", newAccessToken);
      localStorage.setItem("refreshToken", newRefreshToken);
    } else {
      sessionStorage.setItem("userToken", newAccessToken);
      sessionStorage.setItem("refreshToken", newRefreshToken);
    }

    apiClient.defaults.headers.common["Authorization"] = "Bearer " + newAccessToken;
    return newAccessToken;
  } catch {
    return null;
  }
};

// --- REQUEST INTERCEPTOR ---
// Proactively refresh the access token if it is expired BEFORE sending the request.
// This prevents network errors caused by sending a known-expired token.
apiClient.interceptors.request.use(
  async (config) => {
    // Skip refresh logic for the refresh endpoint itself
    if (config.url === "/auth/refresh") return config;

    let token =
      localStorage.getItem("userToken") || sessionStorage.getItem("userToken");

    if (token) {
      // If the access token is expired (or about to expire), refresh it first
      if (isTokenExpired(token)) {
        if (isRefreshing) {
          // Another request is already refreshing — wait for it
          const newToken = await new Promise<string | null>((resolve) => {
            failedQueue.push({ resolve, reject: resolve });
          });
          token = newToken;
        } else {
          isRefreshing = true;
          const newToken = await doRefresh();
          isRefreshing = false;

          if (newToken) {
            processQueue(null, newToken);
            token = newToken;
          } else {
            processQueue(new Error("Token refresh failed"), null);
            // Clear tokens and redirect
            localStorage.removeItem("userToken");
            localStorage.removeItem("refreshToken");
            sessionStorage.removeItem("userToken");
            sessionStorage.removeItem("refreshToken");
            window.location.href = "/login";
            return Promise.reject(new Error("Session expired"));
          }
        }
      }

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } else {
      // Guest user — send session ID instead
      const sessionId = localStorage.getItem("guest_session_id");
      if (sessionId) {
        config.headers["X-Session-ID"] = sessionId;
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);
// --- HẾT PHẦN REQUEST INTERCEPTOR ---

// Add response interceptor to handle errors properly
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Catch genuine 401s from the server (token rejected server-side)
    const is401 =
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      originalRequest.url !== "/auth/refresh";

    if (is401) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers["Authorization"] = "Bearer " + token;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const newToken = await doRefresh();
      isRefreshing = false;

      if (newToken) {
        processQueue(null, newToken);
        originalRequest.headers["Authorization"] = "Bearer " + newToken;
        return apiClient(originalRequest);
      } else {
        processQueue(new Error("Token refresh failed"), null);
        localStorage.removeItem("userToken");
        localStorage.removeItem("refreshToken");
        sessionStorage.removeItem("userToken");
        sessionStorage.removeItem("refreshToken");
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
