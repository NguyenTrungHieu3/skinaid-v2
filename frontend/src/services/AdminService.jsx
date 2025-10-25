import axios  from "axios";

const API_URL = "http://127.0.0.1:8000/api/v1";

const SigninService = {
  login: async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/auth/signin`, {
        email,
        password,
      });

      // Kiểm tra xem BE trả data hay không
      if (!response.data?.data) {
        const beMessage =
          response.data?.message || "Login failed: invalid credentials";
        throw new Error(beMessage);
      }

      const accessToken = response.data.data.access_token;
      const refreshToken = response.data.data.refresh_token;

      localStorage.setItem("token", accessToken);
      if (refreshToken) localStorage.setItem("refreshToken", refreshToken);

      return { token: accessToken, refreshToken };
    } catch (error) {
      // Lấy message từ BE nếu có
      if (error.response && error.response.data) {
        const beMessage =
          error.response.data.message ||
          error.response.data.detail?.message ||
          "Login failed";
        throw new Error(beMessage);
      }

      throw new Error(error.message || "Login failed due to network error");
    }
  },
};

export default SigninService;