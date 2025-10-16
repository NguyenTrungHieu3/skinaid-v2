import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/v1/upload/image";

const UploadImgService = {
   uploadFile: async (file) => {
     const formData = new FormData();
     formData.append("file", file);

     const token = localStorage.getItem("token"); // lấy token đăng nhập

     if (!token) {
       throw new Error("No authentication token found");
     }

     try {
       const response = await axios.post(API_URL, formData, {
         headers: {
           "Content-Type": "multipart/form-data",
           Authorization: `Bearer ${token}`, // gửi token lên backend
         },
       });

       return response.data; // backend trả về { success, message, data?, error_code?, error_details?, timestamp }
     } catch (error) {
       console.error("Upload service error:", error);

       // Re-throw để component xử lý
       if (error.response) {
         // Server trả về lỗi
         throw error;
       } else if (error.request) {
         // Network error
         throw new Error("Network error: Please check your connection");
       } else {
         // Other error
         throw new Error(error.message || "Upload failed");
       }
     }
   },
 };

export default UploadImgService;
