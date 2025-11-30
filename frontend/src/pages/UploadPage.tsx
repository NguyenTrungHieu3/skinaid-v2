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
  FaSearchPlus,
  FaSearchMinus,
} from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { analyzeImage } from "../services/aiService";
import Cropper from "react-easy-crop";
import { getCroppedImg } from "../utils/canvasUtils";
import {
  analyzeImageQuality,
  autoEnhanceImage,
} from "../utils/imageProcessingUtils";
import { useGuestSession } from "../hooks/useGuestSession";

// Cấu hình
const MIN_SIZE_PX = 512;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg"];

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

  // File & Preview
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Crop State
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<any>(null);

  // Quality State
  const [qualityIssues, setQualityIssues] = useState<string[]>([]);
  const [isEnhancing, setIsEnhancing] = useState(false);

  // Ref để tránh xử lý 2 lần
  const hasProcessedRef = useRef(false);

  // --- LOGIC FUNCTIONS ---

  // 1. Check Quality
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

  // 2. Check Technical
  const validateTechnical = useCallback(
    (file: File, url: string) => {
      const img = new Image();
      img.src = url;
      img.onload = () => {
        let issues = [];
        // Sử dụng biến replacement {{size}} cho thông báo lỗi
        if (file.size > MAX_FILE_SIZE)
          issues.push(t("upload_page.error.file_too_large", { size: 10 }));

        const ratio = img.width / img.height;
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

  // 3. Handle File Select
  const handleFileSelect = useCallback(
    (file: File) => {
      setErrorMessage("");
      // Basic validate
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        setErrorMessage(t("upload_page.error.invalid_type"));
        return;
      }

      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setCurrentFile(file);

      // Bắt đầu Flow
      setStep("CHECKING_TECH");
      validateTechnical(file, url);
    },
    [t, validateTechnical]
  );

  // --- USE EFFECT: NHẬN FILE TỪ HEADER ---
  useEffect(() => {
    const state = location.state as LocationState;
    const fileFromState = state?.fileToUpload;

    if (fileFromState && !hasProcessedRef.current) {
      console.log("🚀 Receiving file from Header:", fileFromState.name);
      hasProcessedRef.current = true;
      handleFileSelect(fileFromState);
      window.history.replaceState({}, document.title);
    }
  }, [location, handleFileSelect]);

  // --- CÁC HÀM XỬ LÝ KHÁC ---

  const handleCropConfirm = async () => {
    if (!previewUrl || !croppedAreaPixels) return;
    try {
      const croppedFile = await getCroppedImg(previewUrl, croppedAreaPixels);
      const newUrl = URL.createObjectURL(croppedFile);
      setPreviewUrl(newUrl);
      setCurrentFile(croppedFile);
      validateQuality(newUrl);
    } catch (e) {
      console.error(e);
      setErrorMessage(t("upload_page.error.corrupted")); // Hoặc thông báo lỗi chung
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
      setErrorMessage(t("upload_page.error.corrupted")); // Fallback error
      setStep("READY");
    }
  };

  const handleReset = () => {
    setStep("IDLE");
    setPreviewUrl(null);
    setCurrentFile(null);
    setErrorMessage("");
    setQualityIssues([]);
    hasProcessedRef.current = false;
  };

  // Zoom handlers
  const MIN_ZOOM = 1;
  const MAX_ZOOM = 3;
  const ZOOM_STEP = 0.1;
  const zoomPercentage = ((zoom - MIN_ZOOM) / (MAX_ZOOM - MIN_ZOOM)) * 100;

  const handleZoomIn = () =>
    setZoom((prev) => Math.min(prev + ZOOM_STEP, MAX_ZOOM));
  const handleZoomOut = () =>
    setZoom((prev) => Math.max(prev - ZOOM_STEP, MIN_ZOOM));

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

      {/* CASE 1: IDLE */}
      {step === "IDLE" && (
        <div
          className={`${styles.uploadBox} ${isDragging ? styles.dragging : ""}`}
        >
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

      {/* CASE 2: WORKSPACE */}
      {step !== "IDLE" && (
        <div className={styles.workspace}>
          {/* LEFT: VIEWER */}
          <div className={styles.viewerPanel}>
            {step === "CROP_NEEDED" && previewUrl ? (
              <div className={styles.cropperWrapper}>
                <Cropper
                  image={previewUrl}
                  crop={crop}
                  zoom={zoom}
                  aspect={3 / 4}
                  onCropChange={setCrop}
                  onZoomChange={setZoom}
                  onCropComplete={(_, pixels) => setCroppedAreaPixels(pixels)}
                />
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
              {/* Dùng tạm key loading để làm tiêu đề "Analyzing/Phân tích" */}
              <button
                onClick={handleReset}
                className={styles.btnIcon}
                title={t("upload.btn.retake")}
              >
                <FaRedo />
              </button>
            </div>

            <div className={styles.controlBody}>
              {/* CROP CONTROLS */}
              {step === "CROP_NEEDED" && (
                <div className={styles.panelContent}>
                  <div className={styles.statusBoxWarning}>
                    <FaCropAlt />
                    <span>{t("upload.warning.resize")}</span>
                  </div>
                  <div className={styles.sliderGroup}>
                    <label className={styles.zoomLabel}>
                      {t("upload.label.zoom")}
                    </label>
                    <div className={styles.sliderWrapper}>
                      <button
                        onClick={handleZoomOut}
                        className={styles.sliderIconBtn}
                      >
                        <FaSearchMinus />
                      </button>
                      <input
                        type="range"
                        min={MIN_ZOOM}
                        max={MAX_ZOOM}
                        step={ZOOM_STEP}
                        value={zoom}
                        onChange={(e) => setZoom(Number(e.target.value))}
                        className={styles.zoomBar}
                        style={{
                          background: `linear-gradient(to right, #0d9488 ${zoomPercentage}%, #cbd5e1 ${zoomPercentage}%)`,
                        }}
                      />
                      <button
                        onClick={handleZoomIn}
                        className={styles.sliderIconBtn}
                      >
                        <FaSearchPlus />
                      </button>
                    </div>
                  </div>
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

              {/* REVIEW CONTROLS */}
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

              {/* READY CONTROLS */}
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

              {/* SCANNING LOADING */}
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
