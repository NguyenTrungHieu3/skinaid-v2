import axios from "axios";

// const API_URL = "http://127.0.0.1:8000/api/v1/upload/image";
const API_URL = "http://127.0.0.1:8000/api/v1/ai/analyze";

const UploadImgService = {
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("token"); // lấy token đăng nhập

    try {
      const response = await axios.post(API_URL, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`, // gửi token lên backend
        },
      });
      // backend trả về { success, error_code?, error_message?, file_info? }
      return response.data;
    } catch (error) {
      console.error(
        "Lỗi từ UploadImgService:",
        error.response?.data || error.message
      );
      throw error;
    }
  },
};

export default UploadImgService;
