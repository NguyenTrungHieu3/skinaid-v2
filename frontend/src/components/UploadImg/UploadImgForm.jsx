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

    // ✅ Check client-side trước
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
      const result = await UploadImgService.uploadFile(uploadedFile);
      console.log("Upload result:", result);

      // ✅ Check success từ backend
      if (!result.success) {
        alert(`Upload failed: ${result.error_message}`);
        return;
      }

      // ✅ Dùng result.data thay vì result.file_info
      navigate("/result", {
        state: {
          fileUrl: URL.createObjectURL(uploadedFile),
          result: result.data,
        },
      });
    } catch (err) {
      console.error("Upload error:", err);

      const backendMessage =
        err.response?.data?.error_message ||
        err.response?.data?.detail ||
        err.message ||
        "Upload failed";

      alert(`Upload failed HTTP: ${backendMessage}`);
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
