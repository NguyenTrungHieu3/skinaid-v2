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

// Tạo 1 instance của axios với cấu hình mặc định
const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/v1", // URL gốc của backend

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
    }

    // 3. KHÔNG làm gì với 'Content-Type' cả.
    // Xóa bỏ toàn bộ logic "if (config.data instanceof FormData)..."
    // Hãy để Axios tự động xử lý.

    return config; // 4. Trả về config đã cập nhật
  },
  (error) => {
    // Trả về lỗi nếu có
    return Promise.reject(error);
  }
);
// --- HẾT PHẦN SỬA ---

export default apiClient;
