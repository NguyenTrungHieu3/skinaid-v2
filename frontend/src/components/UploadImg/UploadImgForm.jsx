import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "@fortawesome/fontawesome-free/css/all.min.css";
import UploadImgService from "../../services/UploadImgService";
import ErrorBanner from "../Verify/ErrorBanner";
import "../../assets/styles/UploadImg.scss"; // nhớ import file CSS

function UploadImgForm() {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false); // ✅ thêm state loading
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const location = useLocation();
  const hasOpened = useRef(false);

  useEffect(() => {
    if (
      location.state?.autoOpen &&
      fileInputRef.current &&
      !hasOpened.current
    ) {
      hasOpened.current = true;
      fileInputRef.current.click();
    }
  }, [location.state]);

  const showError = (msg) => setErrorMessage(msg);

  const handleFileChange = async (uploadedFile) => {
    if (!uploadedFile) return;

    const allowedTypes = ["image/jpeg", "image/png"];
    if (!allowedTypes.includes(uploadedFile.type)) {
      showError("Only JPEG and PNG are allowed.");
      return;
    }
    if (uploadedFile.size > 5 * 1024 * 1024) {
      showError("File must be smaller than 5MB.");
      return;
    }

    setFile(uploadedFile);
    setIsLoading(true); // ✅ bật loading

    try {
      const result = await UploadImgService.uploadFile(uploadedFile);
      console.log("Upload result:", result);

      if (!result.success) {
        showError(`Upload failed: ${result.error_message}`);
        setIsLoading(false);
        return;
      }

      navigate("/results", {
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
      showError(`Upload failed HTTP: ${backendMessage}`);
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => handleFileChange(e.target.files[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileChange(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => e.preventDefault() || setIsDragging(true);
  const handleDragLeave = (e) => e.preventDefault() || setIsDragging(false);

  // ✅ GIAI ĐOẠN LOADING
  if (isLoading) {
    return (
      <div className="loading-screen">
        <i className="fa-solid fa-spinner fa-spin"></i>
        <p>Analyzing image, please wait...</p>
      </div>
    );
  }

  return (
    <div className="upload-form">
      <ErrorBanner message={errorMessage} onClose={() => setErrorMessage("")} />

      <div
        className={`upload-box ${isDragging ? "dragging" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
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
          <input
            type="file"
            hidden
            accept=".jpg,.jpeg,.png,.tiff,.webp"
            ref={fileInputRef}
            onChange={handleInputChange}
          />
        </label>
      </div>

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

      {isDragging && (
        <div className="drag-overlay">
          <span>Drop your image here</span>
        </div>
      )}
    </div>
  );
}

export default UploadImgForm;
