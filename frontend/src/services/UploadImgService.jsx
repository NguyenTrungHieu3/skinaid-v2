import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/v1/upload/image";

const UploadImgService = {
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("token"); // lấy token đăng nhập

    const response = await axios.post(API_URL, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        Authorization: `Bearer ${token}`, // gửi token lên backend
      },
    });

    return response.data; // backend trả về { success, error_code?, error_message?, file_info? }
  },
};

export default UploadImgService;
