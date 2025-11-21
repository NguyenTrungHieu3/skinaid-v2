// src/pages/UploadPage.tsx
import React, { useState, useRef, useEffect, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { DragEvent, ChangeEvent } from "react";
import styles from "./UploadPage.module.css"; // Dùng CSS Modules
import {
  FaUpload,
  FaImage,
  FaTimes, // Icon để đóng lỗi
} from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { analyzeImage } from "../services/aiService";
import { isAxiosError } from "axios";

// Định nghĩa các hằng số
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg"];

const MAX_DIMENSION_WIDTH = 4096;
const MAX_DIMENSION_HEIGHT = 4096;

const MIN_DIMENSION_WIDTH = 100;
const MIN_DIMENSION_HEIGHT = 100;

const UploadPage = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- 1. THÊM STATE MỚI ---
  const [isLoading, setIsLoading] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const timerIdRef = useRef<number | null>(null); // Thêm ref để lưu ID của timeout

  // Ref này để đánh dấu xem chúng ta đã bắt đầu xử lý file từ state chưa
  const hasProcessedRef = useRef(false);

  const location = useLocation();
  const navigate = useNavigate();

  const { t } = useTranslation();

  // useEffect(() => {
  //   // Tác dụng 1: Reset state khi location thay đổi
  //   // (Tức là khi user click link "Upload Image" trên header)
  //   console.log("Location changed, resetting UploadPage state.");
  //   setErrorMessage("");
  //   setPreviewImage(null);
  //   setIsLoading(false);

  //   // Tác dụng 2: Dọn dẹp (cleanup) khi rời trang
  //   return () => {
  //     // Dọn dẹp URL và Timeout khi component unmount
  //     if (previewImage) {
  //       URL.revokeObjectURL(previewImage);
  //       console.log("Revoked old preview URL:", previewImage);
  //     }
  //     if (timerIdRef.current) {
  //       clearTimeout(timerIdRef.current);
  //       console.log("Cancelled active API simulation.");
  //     }
  //   };
  // }, [location]);

  const getImageDimensions = (
    file: File
  ): Promise<{ width: number; height: number }> => {
    return new Promise((resolve, reject) => {
      // Tạo một URL tạm thời cho file
      const objectUrl = URL.createObjectURL(file);
      const img = new Image();

      // Hàm này sẽ chạy khi ảnh được tải xong
      img.onload = () => {
        resolve({ width: img.width, height: img.height });
        // Dọn dẹp URL tạm thời
        URL.revokeObjectURL(objectUrl);
      };

      // Hàm này chạy nếu file không phải là ảnh
      img.onerror = () => {
        reject(new Error("Could not read image file."));
        URL.revokeObjectURL(objectUrl);
      };

      // Bắt đầu tải ảnh
      img.src = objectUrl;
    });
  };

  // --- 2. CẬP NHẬT HÀM XỬ LÝ FILE ---
  const processFile = useCallback(
    async (file: File) => {
      // Ngăn upload khi đang xử lý
      // if (isLoading) return;

      // Xóa lỗi cũ ngay khi bắt đầu xử lý file mới
      setErrorMessage("");

      // 1. Kiểm tra kích thước
      if (file.size > MAX_FILE_SIZE) {
        setErrorMessage(t("upload_page.error.file_too_large", { size: 5 }));
        return;
      }
      // 2. Kiểm tra loại file
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        setErrorMessage(t("upload_page.error.invalid_type"));
        return;
      }

      // 3. THÊM BƯỚC KIỂM TRA KÍCH THƯỚC ẢNH (Dimensions)
      try {
        const dimensions = await getImageDimensions(file);
        if (
          dimensions.width > MAX_DIMENSION_WIDTH ||
          dimensions.height > MAX_DIMENSION_HEIGHT ||
          dimensions.width < MIN_DIMENSION_WIDTH || // Thêm check min width
          dimensions.height < MIN_DIMENSION_HEIGHT // Thêm check min height
        ) {
          // CẬP NHẬT LẠI THÔNG BÁO LỖI:
          setErrorMessage(
            t("upload_page.error.dimensions", {
              minW: MIN_DIMENSION_WIDTH,
              minH: MIN_DIMENSION_HEIGHT,
              maxW: MAX_DIMENSION_WIDTH,
              maxH: MAX_DIMENSION_HEIGHT,
            })
          );
          return;
        }
      } catch (error) {
        // Bắt lỗi nếu file bị hỏng hoặc không phải ảnh
        setErrorMessage(t("upload_page.error.corrupted"));
        return;
      }

      // Nếu tất cả đều ổn
      setIsLoading(true);

      // Tạo URL xem trước cho ảnh
      const imageUrl = URL.createObjectURL(file);
      setPreviewImage(imageUrl);

      // --- 3. GIẢ LẬP GỌI API UPLOAD ---
      // (TODO: Thay thế 'setTimeout' bằng lệnh gọi API thật của bạn)
      // Ví dụ: uploadFileToApi(file).then(...)
      console.log("File is valid, simulating upload:", file.name);

      // ... (setTimeout) ...
      // const timerId = setTimeout(() => {
      //   console.log("API call finished.");
      //   setIsLoading(false);

      //   // (Xóa dòng 'revoke' ở đây)

      //   timerIdRef.current = null; // Xóa ID khi đã chạy xong
      // }, 3000);

      // Giả lập API
      // const timerId = setTimeout(() => {
      //   console.log("API call finished.");
      //   setIsLoading(false);
      //   timerIdRef.current = null;
      // }, 3000);

      try {
        const formData = new FormData();
        formData.append("file", file); // Key là "file" (từ curl)

        console.log("File is valid, calling POST /ai/analyze...");
        const response = await analyzeImage(formData); // Gọi API // 5. CHUYỂN TRANG

        if (response.data.success) {
          const analysisId = response.data.data.analysis_id;
          console.log("Analysis successful, navigating to ID:", analysisId); // Chuyển người dùng đến trang kết quả với ID
          navigate(`/analysis-result/${analysisId}`);
        } else {
          setErrorMessage(response.data.message || "Analysis failed.");
          setIsLoading(false);
        }
      } catch (err) {
        console.error("Analysis API error:", err);
        if (isAxiosError(err)) {
          setErrorMessage(
            err.response?.data?.message || "Analysis service error."
          );
        } else {
          setErrorMessage("An unknown error occurred.");
        }
        setIsLoading(false); // Dừng loading khi có lỗi
      }

      // Lưu ID của timeout vào ref
      // timerIdRef.current = timerId as unknown as number; // Hack nhỏ cho TypeScript
    },
    [t, navigate]
  );

  // --- THAY THẾ TOÀN BỘ useEffect CŨ BẰNG 2 useEffect NÀY ---

  // Effect 1: Xử lý file từ navigation HOẶC reset trang
  useEffect(() => {
    const fileFromState = location.state?.fileToUpload as File;

    if (fileFromState && !hasProcessedRef.current) {
      // 1. Nếu CÓ file VÀ chưa xử lý:
      // Đánh dấu là đã xử lý
      hasProcessedRef.current = true;

      console.log("Received file, processing...");
      processFile(fileFromState);

      // Xóa state đi
      navigate(location.pathname, { replace: true, state: {} });
    } else if (!fileFromState && !hasProcessedRef.current) {
      // 2. Nếu KHÔNG có file VÀ chưa xử lý:
      // Đây là trường hợp user tự vào trang, reset state
      console.log("No file, not processing, resetting page.");
      setErrorMessage("");
      setPreviewImage(null);
      setIsLoading(false);
    }
    // 3. Nếu KHÔNG có file NHƯNG ĐÃ xử lý (hasProcessedRef.current = true):
    // Đây là lần chạy thứ 2 (do navigate), KHÔNG LÀM GÌ CẢ.
    // Việc này ngăn logic 'else' chạy và reset state.
  }, [location, navigate, processFile]); // Bỏ 'previewImage'

  // Effect 2: Dọn dẹp (cleanup)
  useEffect(() => {
    // Tác dụng duy nhất của effect này là "đăng ký" 1 hàm dọn dẹp
    // Hàm này sẽ chạy khi component unmount (rời trang)
    return () => {
      if (previewImage) {
        URL.revokeObjectURL(previewImage);
        console.log("Revoked old preview URL:", previewImage);
      }
      if (timerIdRef.current) {
        clearTimeout(timerIdRef.current);
        console.log("Cancelled active API simulation.");
      }
    };
  }, [previewImage]); // <-- Effect này CHỈ phụ thuộc vào 'previewImage'

  // --- CÁC HÀM XỬ LÝ SỰ KIỆN ---

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div
      className={styles.uploadPage}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <div className={styles.uploadForm}>
        {errorMessage && (
          <div className={styles.errorBanner}>
            <span>{errorMessage}</span>
            <button onClick={() => setErrorMessage("")}>
              <FaTimes />
            </button>
          </div>
        )}

        {/* --- 4. CẬP NHẬT JSX (THAY ĐỔI LỚN) --- */}
        <div
          className={`${styles.uploadBox} ${isDragging ? styles.dragging : ""}`}
        >
          {/* Nếu KHÔNG có ảnh xem trước, hiển thị ô upload */}
          {!previewImage ? (
            <label className={styles.uploadDropzone}>
              <div className={styles.uploadIcon}>
                <FaUpload />
                <div className={styles.subIcon}>
                  <FaImage />
                </div>
              </div>
              <h3>{t("upload_page.title")}</h3>
              <p>{t("upload_page.desc")}</p>
              <div className={styles.fileTypes}>
                <span>JPEG</span>
                <span>PNG</span>
                <span>JPG</span>
              </div>
              <p className={styles.fileNote}>{t("upload_page.condition")}</p>
              <input
                type="file"
                hidden
                accept=".jpg,.jpeg,.png"
                ref={fileInputRef}
                onChange={handleInputChange}
                disabled={isLoading} // Thêm disabled
              />
            </label>
          ) : (
            /* Nếu CÓ ảnh xem trước, hiển thị nó */
            <div className={styles.previewContainer}>
              <img
                src={previewImage}
                alt="Wound preview"
                className={styles.previewImage}
              />
              {/* Nếu đang loading, hiển thị lớp phủ */}
              {isLoading && (
                <div className={styles.loadingOverlay}>
                  <div className={styles.loader}></div>
                  <p>{t("upload_page.loading")}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {isDragging && (
        <div className={styles.pageDragOverlay}>
          <FaUpload />
          <h3>{t("upload_page.drop")}</h3>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
