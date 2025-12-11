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

      // DEBUG: Log session_id being sent
      console.log("[API Interceptor] Sending request to:", config.url);
      console.log("[API Interceptor] Session ID in localStorage:", sessionId);

      if (sessionId) {
        config.headers["X-Session-ID"] = sessionId;
      } else {
        console.warn("[API Interceptor] No session_id found in localStorage!");
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

// Add response interceptor to handle errors properly
apiClient.interceptors.response.use(
  (response) => {
    // If response is successful, just return it
    return response;
  },
  (error) => {
    // If there's an error response from the server, preserve it
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      return Promise.reject(error);
    } else if (error.request) {
      // The request was made but no response was received
      return Promise.reject(new Error('Network Error: Unable to reach the server'));
    } else {
      // Something happened in setting up the request that triggered an Error
      return Promise.reject(error);
    }
  }
);

export default apiClient;
