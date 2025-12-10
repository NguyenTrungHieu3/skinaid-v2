import { useRef, type ChangeEvent } from "react";
import styles from "./MainHeader.module.css";
import {
  FaSave,
  FaDownload,
  FaCamera,
  FaChevronDown, // Icon mũi tên cho dropdown
} from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";

type Severity = "Mild" | "Moderate" | "Severe" | string;
type WoundType = "abrasion" | "burn" | "bruise";

// Interface Tab dùng chung (hoặc import từ file types nếu có)
interface Tab {
  id: string;
  title: string;
  severity: Severity;
  type: WoundType;
}

interface MainHeaderProps {
  title: string; // Tiêu đề hiện tại (để hiển thị màu)
  severity?: Severity; // Mức độ hiện tại (để hiển thị màu)

  // --- Props cho Dropdown ---
  tabs?: Tab[]; // Danh sách toàn bộ vết thương
  activeTabId?: string; // ID đang chọn
  onSelectTab?: (id: string) => void; // Hàm xử lý khi chọn

  onDownload?: () => void;
}

const getSeverityClass = (severity: Severity = "") => {
  switch (severity.toLowerCase()) {
    case "mild":
      return styles.titleMild;
    case "moderate":
      return styles.titleModerate;
    case "severe":
      return styles.titleSevere;
    default:
      return styles.titleDefault;
  }
};

const parseWoundTitle = (title: string) => {
  const parts = title.split(/[-\s]+/); // tách theo khoảng trắng hoặc '-'

  return {
    type: parts[0] || "",
    number: parts[1] || "",
    sub_type: parts.slice(2).join(" ") || "",
  };
};

const translateWoundTitle = (title: string, t: any) => {
  const { type, number, sub_type } = parseWoundTitle(title);

  const translatedType = t(`analysis.wound_type_uppercase.${type}`, type);

  const translatedSub =
    sub_type !== "" ? t(`analysis.wound_sub.${sub_type}`, sub_type) : "";

  return `${translatedType} ${number} ${translatedSub}`.trim();
};

const MainHeader = ({
  title,
  severity,
  tabs = [],
  activeTabId,
  onSelectTab,
  onDownload,
}: MainHeaderProps) => {
  const { t } = useTranslation();

  // 2. LẤY TRẠNG THÁI ĐĂNG NHẬP
  const { isAuthenticated } = useAuth();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      navigate("/upload", { state: { fileToUpload: file } });
      e.target.value = "";
    }
  };

  // Logic xử lý khi chọn item trong dropdown
  const handleWoundChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (onSelectTab) {
      onSelectTab(e.target.value);
    }
  };

  return (
    <div className={styles.mainHeader}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept="image/png, image/jpeg, image/jpg"
      />

      <div className={styles.titleWrapper}>
        {/* NẾU CÓ NHIỀU VẾT THƯƠNG -> HIỆN DROPDOWN */}
        {tabs.length > 1 ? (
          <div
            className={`${styles.selectContainer} ${getSeverityClass(
              severity
            )}`}
          >
            <select
              value={activeTabId}
              onChange={handleWoundChange}
              className={styles.woundSelect}
            >
              {tabs.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {translateWoundTitle(tab.title, t)}
                </option>
              ))}
            </select>
            <FaChevronDown className={styles.selectIcon} />
          </div>
        ) : (
          /* NẾU CHỈ CÓ 1 VẾT THƯƠNG -> HIỆN TITLE THƯỜNG */
          <h1 className={`${styles.pageTitle} ${getSeverityClass(severity)}`}>
            {translateWoundTitle(title, t)}
          </h1>
        )}
      </div>

      <div className={styles.mainActions}>
        <button
          className={`${styles.actionBtn} ${styles.uploadBtnPrimary}`}
          onClick={handleUploadClick}
        >
          <FaCamera />
          <span className={styles.btnText}>
            {t("analysis.header_upload_button")}
          </span>
        </button>

        {/* 3. CHỈ HIỂN THỊ NÚT SAVE KHI CHƯA ĐĂNG NHẬP (!isAuthenticated) */}
        {!isAuthenticated && (
          <button className={styles.actionBtn}>
            <FaSave />
            <span className={styles.btnText}>
              {t("analysis.header_save_button")}
            </span>
          </button>
        )}

        {onDownload && (
          <button className={styles.actionBtn} onClick={onDownload}>
            <FaDownload />{" "}
            <span className={styles.btnText}>
              {t("analysis.header_download_button")}
            </span>
          </button>
        )}

        {/* <button className={`${styles.actionBtn} ${styles.btnIcon}`}>
          <FaHeart />
        </button> */}
      </div>
    </div>
  );
};

export default MainHeader;
