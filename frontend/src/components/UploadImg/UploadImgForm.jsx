import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "@fortawesome/fontawesome-free/css/all.min.css";
import UploadImgService from "../../services/UploadImgService";

function UploadImgForm() {
  const [file, setFile] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;

    const allowedTypes = ["image/jpeg", "image/png"];
    if (!allowedTypes.includes(uploadedFile.type)) {
      alert("Only JPEG and PNG are allowed.");
      return;
    }
    if (uploadedFile.size > 5 * 1024 * 1024) {
      alert("File must be smaller than 5MB.");
      return;
    }

    setFile(uploadedFile);

    try {
       const token = localStorage.getItem("token");
       if (!token) {
         alert("Please log in to upload images");
         navigate("/signin");
         return;
       }

       const result = await UploadImgService.uploadFile(uploadedFile);
       console.log("Upload result:", result);

       if (!result.success) {
         console.error("Upload failed with response:", result);
         alert(`Upload failed: ${result.message}`);
         return;
       }

       console.log("Upload successful, navigating to result page...");

      navigate("/result", {
        state: {
          fileUrl: URL.createObjectURL(uploadedFile),
          result: result.data,
          imageInfo: result.data?.image_information,
          aiResult: result.data?.ai_result,
          firstAid: result.data?.first_aid,
        },
      });
    } catch (err) {
       console.error("Upload error:", err);

       let backendMessage = "Upload failed";

       if (err.response) {
         // Server trả về lỗi
         if (err.response.data?.message) {
           backendMessage = err.response.data.message;
         } else if (err.response.data?.error_message) {
           backendMessage = err.response.data.error_message;
         } else if (err.response.data?.detail) {
           backendMessage = err.response.data.detail;
         } else if (err.response.status === 401) {
           backendMessage = "Unauthorized: Please log in again";
         } else if (err.response.status === 403) {
           backendMessage = "Forbidden: Account verification required";
         } else if (err.response.status >= 500) {
           backendMessage = "Server error: Please try again later";
         } else {
           backendMessage = `Server error (${err.response.status})`;
         }
       } else if (err.request) {
         // Network error
         backendMessage = "Network error: Please check your connection";
       } else {
         // Other error
         backendMessage = err.message || "Upload failed";
       }

       alert(`Upload failed: ${backendMessage}`);
     }
  };

  return (
    <div className="upload-form">
      {/* Upload Box */}
      <div className="upload-box">
        <label className="upload-dropzone">
          <div className="upload-icon">
            <i className="fa-solid fa-arrow-up-from-bracket"></i>
            <div className="sub-icon">
              <i className="fa-solid fa-image"></i>
            </div>
          </div>
          <h3>Upload Skin Wound Image</h3>
          <p>
            Drag and drop your medical images here, or click to browse your
            device
          </p>

          <div className="file-types">
            <span>JPEG</span>
            <span>PNG</span>
            <span>TIFF</span>
            <span>WebP</span>
          </div>

          <p className="file-note">Maximum file size: 5MB per image</p>
          <input type="file" hidden onChange={handleFileChange} />
        </label>
      </div>

      {/* Footer */}
      <div className="upload-footer">
        <h4>Ready for Wound Documentation</h4>
        <p>
          Upload your wound images to begin secure documentation and AI-powered
          analysis. All data is encrypted and handled with medical-grade
          privacy.
        </p>
        <div className="features">
          <span>🔒 Secure</span>
          <span>🛡️ Encrypted</span>
          <span>🤖 AI-Powered</span>
        </div>
        <p className="copyright">© 2025 SkinAid. All rights reserved.</p>
      </div>
    </div>
  );
}

export default UploadImgForm;
