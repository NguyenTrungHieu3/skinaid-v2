import axios from "axios";
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
// Ví dụ: VITE_API_URL = "http://18.179.57.221:8000/api/v1" => BACKEND_URL = "http://18.179.57.221:8000"
export const BACKEND_URL = API_BASE_URL.replace("/api/v1", "");

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

// --- INTERCEPTOR (ĐÃ ĐƠN GIẢN HÓA) ---
// Thêm một "interceptor" để tự động gắn token vào MỌI request
apiClient.interceptors.request.use(
  (config) => {
    // 1. Lấy token từ localStorage hoặc sessionStorage
    const token =
      localStorage.getItem("userToken") || sessionStorage.getItem("userToken");

    // 2. Nếu có token, gắn nó vào header
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      // 3. Nếu KHÔNG có token (guest user), gửi session_id
      const sessionId = localStorage.getItem("guest_session_id");
      if (sessionId) {
        config.headers["X-Session-ID"] = sessionId;
      }
    }

    // 4. KHÔNG làm gì với 'Content-Type' cả.
    // Xóa bỏ toàn bộ logic "if (config.data instanceof FormData)..."
    // Hãy để Axios tự động xử lý.

    return config; // 5. Trả về config đã cập nhật
  },
  (error) => {
    // Trả về lỗi nếu có
    return Promise.reject(error);
  }
);
// --- HẾT PHẦN SỬA ---

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

// Add response interceptor to handle errors properly
apiClient.interceptors.response.use(
  (response) => {
    // If response is successful, just return it
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Check if the error is 401 and the request wasn't already retried
    if (
      error.response &&
      error.response.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      originalRequest.url !== "/auth/refresh"
    ) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers["Authorization"] = "Bearer " + token;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken =
        localStorage.getItem("refreshToken") ||
        sessionStorage.getItem("refreshToken");

      if (!refreshToken) {
        processQueue(error, null);
        isRefreshing = false;
        localStorage.removeItem("userToken");
        localStorage.removeItem("refreshToken");
        sessionStorage.removeItem("userToken");
        sessionStorage.removeItem("refreshToken");
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = data.data.access_token;
        const newRefreshToken = data.data.refresh_token;

        // Determine which storage to update based on where the refresh token was found,
        // not the (possibly expired/cleared) access token.
        if (localStorage.getItem("refreshToken")) {
          localStorage.setItem("userToken", newAccessToken);
          localStorage.setItem("refreshToken", newRefreshToken);
        } else {
          sessionStorage.setItem("userToken", newAccessToken);
          sessionStorage.setItem("refreshToken", newRefreshToken);
        }

        apiClient.defaults.headers.common["Authorization"] = "Bearer " + newAccessToken;
        originalRequest.headers["Authorization"] = "Bearer " + newAccessToken;

        processQueue(null, newAccessToken);
        isRefreshing = false;

        return apiClient(originalRequest);
      } catch (err: any) {
        processQueue(err, null);
        isRefreshing = false;

        localStorage.removeItem("userToken");
        localStorage.removeItem("refreshToken");
        sessionStorage.removeItem("userToken");
        sessionStorage.removeItem("refreshToken");

        window.location.href = "/login";
        return Promise.reject(err);
      }
    }

    if (error.response) {
      return Promise.reject(error);
    } else if (error.request) {
      return Promise.reject(new Error("Network Error: Unable to reach the server"));
    } else {
      return Promise.reject(error);
    }
  }
);

export default apiClient;
