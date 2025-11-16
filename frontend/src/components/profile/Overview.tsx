// src/components/profile/Overview.tsx
import React, { useRef, type ChangeEvent } from "react"; // <-- THÊM useRef, ChangeEvent
import { useNavigate } from "react-router-dom"; // <-- THÊM useNavigate
import styles from "../../pages/ProfilePage.module.css";
import { FaHistory, FaUpload, FaFileExport } from "react-icons/fa";
import { useTranslation } from "react-i18next";
// TODO: Sau này bạn sẽ định nghĩa kiểu dữ liệu này ở file riêng
// (ví dụ: src/types/analysis.ts)
type Analysis = {
  id: string;
  type: string;
  location: string;
  severity: "mild" | "medium" | "severe"; // Chỉ chấp nhận 3 giá trị này
  timestamp: string;
};

// TODO: Dữ liệu này sẽ được lấy từ API hoặc truyền qua props
const mockAnalyses: Analysis[] = [
  {
    id: "1",
    type: "Abrasion (Vết trầy)",
    location: "Left Knee",
    severity: "severe",
    timestamp: "Today, 2:30 PM",
  },
  {
    id: "2",
    type: "Burn (Vết bỏng)",
    location: "Right Hand",
    severity: "medium",
    timestamp: "Yesterday, 10:15 AM",
  },
  {
    id: "3",
    type: "Cut (Vết cắt)",
    location: "Forearm",
    severity: "mild",
    timestamp: "Nov 4, 2025",
  },
];

// --- HÀM HỖ TRỢ CHỌN MÀU SẮC ---
// Hàm này nhận vào severity và trả về class CSS tương ứng
const getSeverityClass = (severity: "mild" | "medium" | "severe") => {
  switch (severity) {
    case "mild":
      return styles.mild;
    case "medium":
      return styles.medium;
    case "severe":
      return styles.severe;
    default:
      return ""; // Mặc định
  }
};

const Overview = () => {
  const navigate = useNavigate(); // <-- Khởi tạo hook navigate
  const fileInputRef = useRef<HTMLInputElement>(null); // <-- Ref cho input ẩn

  const { t } = useTranslation();

  /**
   * Xử lý khi người dùng đã chọn file.
   * Đây là lúc chuyển trang.
   */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (file) {
      // Chuyển hướng đến trang /upload
      // và truyền file qua 'state' của navigation
      console.log("File selected, navigating to /upload with file state...");
      navigate("/upload", { state: { fileToUpload: file } });
    }
  };

  /**
   * Kích hoạt input file ẩn khi bấm nút
   */
  const handleUploadClick = () => {
    // Reset input để user có thể chọn lại file cũ
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    fileInputRef.current?.click();
  };

  return (
    <div className={styles.overviewWrapper}>
      {/* Cột trái: Recent Analyses */}
      <section className={styles.recentAnalyses}>
        <div className={styles.sectionHeader}>
          <h2>
            <FaHistory className={styles.sectionHeaderIcon} />{" "}
            {t("overview.recent_analyses")}
          </h2>
          <a href="#">{t("overview.view_all")}</a>
        </div>
        {/* --- DANH SÁCH RENDER ĐỘNG --- */}
        <div className={styles.analysesList}>
          {/* Kiểm tra nếu không có dữ liệu */}
          {mockAnalyses.length === 0 ? (
            <p>{t("overview.no_data")}</p>
          ) : (
            // Dùng .map() để lặp qua mảng dữ liệu
            mockAnalyses.map((analysis) => (
              <div key={analysis.id} className={styles.analysisItem}>
                <div className={styles.itemInfo}>
                  <h4>{analysis.type}</h4>
                  <p>{analysis.location}</p>
                </div>
                <div className={styles.itemStatus}>
                  {/* Sử dụng hàm getSeverityClass để lấy class động */}
                  <span
                    className={`${styles.statusTag} ${getSeverityClass(
                      analysis.severity
                    )}`}
                  >
                    {/* Hiển thị chữ: "mild" -> "Mild" */}
                    {analysis.severity.charAt(0).toUpperCase() +
                      analysis.severity.slice(1)}
                  </span>
                  <span className={styles.time}>{analysis.timestamp}</span>
                </div>
                {/* TODO: Cập nhật link này với ID của analysis */}
                <a
                  href={`/analysis/${analysis.id}`}
                  className={styles.viewLink}
                >
                  {t("overview.view")}
                </a>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Cột phải: Quick Actions */}
      <aside className={styles.quickActions}>
        <h3>{t("overview.quick_actions")}</h3>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: "none" }}
          accept="image/png, image/jpeg, image/jpg"
        />

        <button
          className={`${styles.actionBtn} ${styles.primary}`}
          onClick={handleUploadClick}
        >
          <FaUpload /> {t("overview.upload_new_image")}
        </button>
        <button className={styles.actionBtn}>
          <FaFileExport /> {t("overview.export_report")}
        </button>
        {/* <button className={styles.actionBtn}>
          <FaCalendarPlus /> Schedule Check
        </button> */}

        {/* <div className={styles.nextCheckup}>
          <h4>Next Check-up</h4>
          <p>Monday, Nov 6, 2025</p>
          <span>2 days remaining</span>
        </div> */}
      </aside>
    </div>
  );
};

export default Overview;
