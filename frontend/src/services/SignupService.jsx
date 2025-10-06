import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/v1";

const SignupService = {
  register: async (formData) => {
    try {
      const payload = {
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword,
      };

      console.log("📤 Sending register payload:", payload);

      const response = await axios.post(`${API_URL}/auth/signup`, payload, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log("✅ Register success:", response.data);

      return response.data;
    } catch (error) {
      console.error("❌ Register error:", error);

      // Lấy lỗi chi tiết từ backend
      let beMessage =
        error.response?.data?.message ||
        error.response?.data?.detail?.message ||
        "Register failed";

      let beDetails = error.response?.data?.error_details || null;

      throw new Error(JSON.stringify({ message: beMessage, details: beDetails }));
    }
  },
};

export default SignupService;
