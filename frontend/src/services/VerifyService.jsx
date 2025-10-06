import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/v1";

const VerifyService = {
  verifyEmail: async (email, token) => {
    try {
      console.log("📤 Verifying email:", email, "with token:", token.substring(0, 20) + "...");
      
      const response = await axios.get(`${API_URL}/auth/verify-email`, {
        params: {
          email: email,
          token: token,
        },
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log("✅ Email verification success:", response.data);
      return response.data;
    } catch (error) {
      console.error("❌ Email verification error:", error);

      throw {
        message:
          error.response?.data?.message ||
          error.response?.data?.detail ||
          error.message ||
          "Email verification failed",
        code:
          error.response?.data?.error_code ||
          error.response?.status ||
          "VERIFICATION_ERROR",
        details: error.response?.data || null,
      };
    }
  },
};

export default VerifyService;