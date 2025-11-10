// import axios from "axios";

// const API_URL = "http://127.0.0.1:8000/api/v1";

// const SigninService = {
//   login: async (email, password) => {
//     try {
//       const response = await axios.post(`${API_URL}/auth/signin`, {
//         email,
//         password,
//       });

//       console.log("Full response.data:", response.data);

//       const accessToken = response.data.data.access_token; // ✅ lấy đúng token
//       const refreshToken = response.data.data.refresh_token;

//       // Lưu token
//       localStorage.setItem("token", accessToken);
//       localStorage.setItem("refreshToken", refreshToken);

//       return { token: accessToken, refreshToken };
//     } catch (error) {
//       console.error("Login error:", error);
//       throw error;
//     }
//   },
// };

// export default SigninService;

import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/v1";

const SigninService = {
  login: async (username, password) => {
    try {
      const response = await axios.post(`${API_URL}/auth/signin`, {
        user_name: username,
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
      const user = response.data.data.user; // Get user data including roles

      // Save tokens and user data
      localStorage.setItem("token", accessToken);
      if (refreshToken) localStorage.setItem("refreshToken", refreshToken);
      if (user) localStorage.setItem("user", JSON.stringify(user));

      return { 
        token: accessToken, 
        refreshToken,
        user // Return user data including roles
      };
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

