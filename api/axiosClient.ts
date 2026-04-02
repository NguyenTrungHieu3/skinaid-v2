import axios from "axios";
import * as SecureStore from "expo-secure-store";

const axiosClient = axios.create({
  baseURL: "http://54.82.244.233/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Tự động thêm token vào mỗi request nếu có
axiosClient.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync("userToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default axiosClient;
