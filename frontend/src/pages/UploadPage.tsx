// src/pages/UploadPage.tsx
import { useState, useRef, useEffect, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import styles from "./UploadPage.module.css";
import {
  FaUpload,
  FaImage,
  FaTimes,
  FaCheck,
  FaMagic,
  FaExclamationTriangle,
  FaArrowRight,
  FaCropAlt,
  FaRedo,
} from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { analyzeImage } from "../services/aiService";

// --- THAY ĐỔI IMPORT Ở ĐÂY ---
// Xóa import Cropper cũ, thêm ReactCrop
import ReactCrop, {
  type Crop,
  type PixelCrop,
  centerCrop,
  makeAspectCrop,
} from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css"; // Import CSS mặc định

import { getCroppedImg } from "../utils/canvasUtils";
import {
  analyzeImageQuality,
  autoEnhanceImage,
} from "../utils/imageProcessingUtils";
import { useGuestSession } from "../hooks/useGuestSession";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg"];

// Hàm hỗ trợ để tạo khung crop mặc định ở giữa ảnh
function centerAspectCrop(
  mediaWidth: number,
  mediaHeight: number,
  aspect?: number
) {
  return centerCrop(
    makeAspectCrop(
      {
        unit: "%",
        width: 80, // Mặc định chiếm 80% chiều rộng
      },
      aspect || 16 / 9, // Tỷ lệ khởi tạo (không bắt buộc khóa)
      mediaWidth,
      mediaHeight
    ),
    mediaWidth,
    mediaHeight
  );
}

type ProcessStep =
  | "IDLE"
  | "CHECKING_TECH"
  | "CROP_NEEDED"
  | "CHECKING_QUALITY"
  | "REVIEW"
  | "READY"
  | "UPLOADING";

interface LocationState {
  fileToUpload?: File;
}

const UploadPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  useGuestSession();

  // --- STATE ---
  const [step, setStep] = useState<ProcessStep>("IDLE");
  const [errorMessage, setErrorMessage] = useState("");

  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // --- CROP STATE MỚI (React-Image-Crop) ---
  const [crop, setCrop] = useState<Crop>(); // State cho UI crop
  const [completedCrop, setCompletedCrop] = useState<PixelCrop | null>(null); // State chứa pixel thực tế để cắt
  const imgRef = useRef<HTMLImageElement>(null); // Ref tới thẻ img để lấy kích thước thật

  const [qualityIssues, setQualityIssues] = useState<string[]>([]);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const hasProcessedRef = useRef(false);

  // --- LOGIC FUNCTIONS ---

  const validateQuality = useCallback(
    async (url: string) => {
      setStep("CHECKING_QUALITY");
      try {
        const result = await analyzeImageQuality(url);
        const issues: string[] = [];
        if (result.isBlurry) issues.push(t("upload.issue.blur"));
        if (result.brightness === "dark") issues.push(t("upload.issue.dark"));
        if (result.brightness === "bright")
          issues.push(t("upload.issue.bright"));

        setTimeout(() => {
          if (issues.length > 0) {
            setQualityIssues(issues);
            setStep("REVIEW");
          } else {
            setQualityIssues([]);
            setStep("READY");
          }
        }, 1200);
      } catch (e) {
        console.error(e);
        setStep("READY");
      }
    },
    [t]
  );

  const validateTechnical = useCallback(
    (file: File, url: string) => {
      const img = new Image();
      img.src = url;
      img.onload = () => {
        let issues = [];
        if (file.size > MAX_FILE_SIZE)
          issues.push(t("upload_page.error.file_too_large", { size: 10 }));

        const ratio = img.width / img.height;
        // Logic cũ: nếu tỷ lệ xấu thì bắt crop
        if (ratio < 0.5 || ratio > 2) issues.push("Bad aspect ratio");

        setTimeout(() => {
          if (issues.length > 0) {
            setErrorMessage(t("upload_page.error.resize_needed"));
            setStep("CROP_NEEDED");
          } else {
            validateQuality(url);
          }
        }, 800);
      };
    },
    [t, validateQuality]
  );

  const handleFileSelect = useCallback(
    (file: File) => {
      setErrorMessage("");
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        setErrorMessage(t("upload_page.error.invalid_type"));
        return;
      }
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setCurrentFile(file);
      setStep("CHECKING_TECH");
      validateTechnical(file, url);
    },
    [t, validateTechnical]
  );

  useEffect(() => {
    const state = location.state as LocationState;
    const fileFromState = state?.fileToUpload;
    if (fileFromState && !hasProcessedRef.current) {
      hasProcessedRef.current = true;
      handleFileSelect(fileFromState);
      window.history.replaceState({}, document.title);
    }
  }, [location, handleFileSelect]);

  // --- XỬ LÝ ẢNH KHI LOAD ĐỂ TẠO KHUNG CROP MẶC ĐỊNH ---
  function onImageLoad(e: React.SyntheticEvent<HTMLImageElement>) {
    const { width, height } = e.currentTarget;
    // Tạo khung crop mặc định ở giữa, không khóa tỷ lệ
    setCrop(centerAspectCrop(width, height, undefined));
  }

  // --- XÁC NHẬN CROP (Đã sửa để dùng completedCrop) ---
  // --- XÁC NHẬN CROP (Đã sửa tỷ lệ Scale) ---
  const handleCropConfirm = async () => {
    // Cần cả URL, pixelCrop và Ref ảnh
    if (!previewUrl || !completedCrop || !imgRef.current) return;

    const image = imgRef.current; // Lấy thẻ img thực tế đang hiển thị

    // 1. Tính tỷ lệ giữa kích thước gốc (natural) và kích thước hiển thị (client)
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    // 2. Quy đổi toạ độ crop từ màn hình sang toạ độ thực tế của ảnh gốc
    const realPixelCrop = {
      x: completedCrop.x * scaleX,
      y: completedCrop.y * scaleY,
      width: completedCrop.width * scaleX,
      height: completedCrop.height * scaleY,
      unit: "px", // Đảm bảo đơn vị là pixel
    };

    try {
      // 3. Gửi toạ độ chuẩn xác đi cắt
      const croppedFile = await getCroppedImg(previewUrl, realPixelCrop);

      const newUrl = URL.createObjectURL(croppedFile);
      setPreviewUrl(newUrl);
      setCurrentFile(croppedFile);
      validateQuality(newUrl);
    } catch (e) {
      console.error(e);
      setErrorMessage(t("upload_page.error.corrupted"));
    }
  };

  const handleEnhance = async () => {
    if (!previewUrl) return;
    setIsEnhancing(true);
    try {
      const enhancedUrl = await autoEnhanceImage(previewUrl);
      const res = await fetch(enhancedUrl);
      const blob = await res.blob();
      const file = new File([blob], "enhanced.jpg", { type: "image/jpeg" });
      setPreviewUrl(enhancedUrl);
      setCurrentFile(file);
      setQualityIssues([]);
      setStep("READY");
    } catch (e) {
      setErrorMessage(t("upload_page.error.corrupted"));
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleSubmit = async () => {
    if (!currentFile) return;
    setStep("UPLOADING");
    const formData = new FormData();
    formData.append("file", currentFile);
    try {
      const response = await analyzeImage(formData);
      if (response.data.success) {
        navigate(`/analysis-result/${response.data.data.analysis_id}`);
      } else {
        setErrorMessage(response.data.message);
        setStep("READY");
      }
    } catch (error) {
      setErrorMessage(t("upload_page.error.corrupted"));
      setStep("READY");
    }
  };

  const handleReset = () => {
    setStep("IDLE");
    setPreviewUrl(null);
    setCurrentFile(null);
    setErrorMessage("");
    setQualityIssues([]);
    setCrop(undefined); // Reset crop
    hasProcessedRef.current = false;
  };

  const handleManualCrop = () => {
    setStep("CROP_NEEDED");
  };

  // Drag handlers
  const [isDragging, setIsDragging] = useState(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files[0]) handleFileSelect(e.dataTransfer.files[0]);
  };

  const isScanning =
    step === "CHECKING_TECH" ||
    step === "CHECKING_QUALITY" ||
    step === "UPLOADING";

  return (
    <div
      className={styles.pageContainer}
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setIsDragging(false);
      }}
    >
      <title>{t("title.upload_page")}</title>

      {errorMessage && (
        <div className={styles.topErrorBanner}>
          <span className={styles.errorContent}>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage("")}
            className={styles.errorExit}
          >
            <FaTimes />
          </button>
        </div>
      )}

      {step === "IDLE" && (
        <div
          className={`${styles.uploadBox} ${isDragging ? styles.dragging : ""}`}
        >
          {/* ... Giữ nguyên phần IDLE ... */}
          <label className={styles.uploadDropzone}>
            <div className={styles.uploadIcon}>
              <FaUpload />
              <div className={styles.subIcon}>
                <FaImage />
              </div>
            </div>
            <h3 className={styles.uploadTitle}>{t("upload_page.title")}</h3>
            <p className={styles.uploadSubTitle}>{t("upload_page.desc")}</p>
            <div className={styles.fileTypes}>
              <span>JPEG</span>
              <span>PNG</span>
              <span>JPG</span>
            </div>
            <p className={styles.uploadCondition}>
              {t("upload_page.condition")}
            </p>
            <input
              type="file"
              hidden
              accept="image/*"
              onChange={(e) =>
                e.target.files?.[0] && handleFileSelect(e.target.files[0])
              }
            />
          </label>
        </div>
      )}

      {step !== "IDLE" && (
        <div className={styles.workspace}>
          {/* LEFT: VIEWER */}
          <div className={styles.viewerPanel}>
            {step === "CROP_NEEDED" && previewUrl ? (
              <div className={styles.cropperWrapper}>
                {/* --- THAY THẾ CROPPER BẰNG REACTCROP --- */}
                <ReactCrop
                  crop={crop}
                  // QUAN TRỌNG: Dùng tham số thứ nhất (c) là pixelCrop để khớp với minWidth/minHeight
                  onChange={(c) => setCrop(c)}
                  onComplete={(c) => setCompletedCrop(c)}
                  // Cấu hình giới hạn
                  minWidth={100} // Không cho thu nhỏ chiều rộng dưới 100px
                  minHeight={100} // Không cho thu nhỏ chiều cao dưới 100px
                  keepSelection={true} // Không cho phép xóa vùng chọn khi click ra ngoài
                  ruleOfThirds={true} // (Tùy chọn) Hiện lưới quy tắc 1/3 để dễ căn chỉnh
                  className={styles.reactCropCustom}
                >
                  <img
                    ref={imgRef}
                    src={previewUrl}
                    alt="Crop me"
                    onLoad={onImageLoad}
                    style={{
                      maxHeight: "75vh",
                      maxWidth: "100%",
                      objectFit: "contain",
                    }} // Đảm bảo ảnh không tràn
                  />
                </ReactCrop>
              </div>
            ) : (
              <div className={styles.imagePreviewWrapper}>
                <img
                  src={previewUrl!}
                  alt="Preview"
                  className={styles.mainImage}
                />
                {isScanning && (
                  <div className={styles.scanningOverlay}>
                    <div className={styles.scanLine}></div>
                    <div className={styles.scanMessage}>
                      {t("upload.status.scanning")}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* RIGHT: CONTROLS */}
          <div className={styles.controlsPanel}>
            <div className={styles.controlHeader}>
              <h4>{t("upload_page.loading").replace("...", "")}</h4>
              <div className={styles.headerBtnGroup}>
                {step !== "CROP_NEEDED" && step !== "UPLOADING" && (
                  <button
                    onClick={handleManualCrop}
                    className={styles.btnIcon}
                    title={t("upload.btn.crop")}
                  >
                    <FaCropAlt />
                  </button>
                )}
                <button
                  onClick={handleReset}
                  className={styles.btnIcon}
                  title={t("upload.btn.retake")}
                >
                  <FaRedo />
                </button>
              </div>
            </div>

            <div className={styles.controlBody}>
              {/* CROP CONTROLS - ĐÃ BỎ ZOOM SLIDER */}
              {step === "CROP_NEEDED" && (
                <div className={styles.panelContent}>
                  <div className={styles.statusBoxWarning}>
                    <FaCropAlt />
                    <span>{t("upload.warning.resize")}</span>
                  </div>

                  {/* Hướng dẫn ngắn gọn */}
                  <p className={styles.note}>
                    Kéo các góc khung hình để chọn vùng ảnh mong muốn.
                  </p>

                  <div className={styles.actionGroup}>
                    <button
                      onClick={handleCropConfirm}
                      className={styles.btnPrimary}
                    >
                      {t("upload.btn.confirm_crop")}
                    </button>
                  </div>
                </div>
              )}

              {/* ... CÁC PHẦN REVIEW VÀ READY GIỮ NGUYÊN ... */}
              {step === "REVIEW" && (
                <div className={styles.panelContent}>
                  <div className={styles.statusBoxDanger}>
                    <FaExclamationTriangle />
                    <span>{t("upload.warning.quality")}</span>
                  </div>
                  <ul className={styles.issueList}>
                    {qualityIssues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                  <div className={styles.suggestionBox}>
                    <p className={styles.suggestionBoxTip}>
                      {t("upload.note.enhance_tip")}
                    </p>
                    <button
                      onClick={handleEnhance}
                      disabled={isEnhancing}
                      className={styles.btnMagic}
                    >
                      <FaMagic />{" "}
                      {isEnhancing
                        ? t("upload.btn.enhancing")
                        : t("upload.btn.enhance")}
                    </button>
                  </div>
                  <div className={styles.divider}>OR</div>
                  <div className={styles.actionGroup}>
                    <button
                      onClick={handleReset}
                      className={styles.btnSecondary}
                    >
                      {t("upload.btn.retake")}
                    </button>
                    <button
                      onClick={() => setStep("READY")}
                      className={styles.btnLink}
                    >
                      {t("upload.btn.ignore")}
                    </button>
                  </div>
                </div>
              )}

              {step === "READY" && (
                <div className={styles.panelContent}>
                  <div className={styles.statusBoxSuccess}>
                    <FaCheck />
                    <span>{t("upload.status.ready")}</span>
                  </div>
                  <p className={styles.note}>{t("upload.note.ready_tip")}</p>
                  <div className={styles.actionGroup}>
                    <button
                      onClick={handleSubmit}
                      className={styles.btnPrimaryLarge}
                    >
                      {t("upload.btn.analyze")} <FaArrowRight />
                    </button>
                  </div>
                </div>
              )}

              {isScanning && (
                <div className={styles.panelContent}>
                  <div className={styles.loaderSpinner}></div>
                  <p className={styles.centerText}>
                    {t("upload.status.scanning")}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {isDragging && (
        <div className={styles.dragOverlay}>
          <FaUpload /> {t("upload_page.drop")}
        </div>
      )}
    </div>
  );
};

export default UploadPage;
