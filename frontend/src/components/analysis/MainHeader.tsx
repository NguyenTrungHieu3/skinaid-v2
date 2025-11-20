import styles from "./MainHeader.module.css";
import { FaSave, FaDownload, FaHeart } from "react-icons/fa";

// 1. (Tùy chọn) Định nghĩa các mức độ
type Severity = "Mild" | "Moderate" | "Severe" | string;

interface MainHeaderProps {
  title: string;
  severity?: Severity; // <-- 2. Thêm prop 'severity'
  // Optional: supply data to be exported by the ExportGuide modal
  exportData?: any;
  exportImageUrl?: string;
}

// 3. Hàm helper để lấy class màu dựa trên severity
const getSeverityClass = (severity: Severity = "") => {
  // Chuyển về chữ thường để khớp (ví dụ: "Mild" -> "mild")
  switch (severity.toLowerCase()) {
    case "mild":
      return styles.titleMild;
    case "moderate":
      return styles.titleModerate;
    case "severe":
      return styles.titleSevere;
    default:
      return styles.titleDefault; // Màu cam mặc định
  }
};

const MainHeader = ({ title, severity}: MainHeaderProps) => {

  return (
    <div className={styles.mainHeader}>
      <h1 className={`${styles.pageTitle} ${getSeverityClass(severity)}`}>
        {title}
      </h1>
      <div className={styles.mainActions}>
        <button className={styles.actionBtn}>
          <FaSave /> Save
        </button>
        <button 
          className={styles.actionBtn}
        >
          <FaDownload /> Download Report
        </button>
        
        <button className={`${styles.actionBtn} ${styles.btnIcon}`}>
          <FaHeart />
        </button>
      </div>
    </div>
  );
};

export default MainHeader;
