import axios from "axios";

// Tạo 1 instance của axios với cấu hình mặc định
const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/v1", // URL gốc của backend

  // KHÔNG set "Content-Type" mặc định ở đây
});

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
