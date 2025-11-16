import styles from "./AnalysisSidebar.module.css"; // File CSS mới
import { FaCheckCircle, FaUpload } from "react-icons/fa";
import React, { useRef, type ChangeEvent } from "react"; // <-- 1. IMPORT THÊM
import { Link, useNavigate } from "react-router-dom";
import Logo from "../../assets/images/general/logo.png"; // Giả sử bạn có logo ở đây
import { useTranslation } from "react-i18next";

// --- Định nghĩa Types (Kiểu dữ liệu) cho props ---
interface SummaryCounts {
  total: number;
  abrasion: number;
  burn: number;
  bruise: number;
}
type Severity = "Mild" | "Moderate" | "Severe" | string;
type WoundType = "abrasion" | "burn" | "bruise";

interface Tab {
  id: string;
  title: string;
  severity: Severity;
  type: WoundType;
}
interface AnalysisSidebarProps {
  summaryCounts: SummaryCounts;
  tabData: Tab[];
  activeTab: string;
  onTabClick: (id: string) => void;
  activeMainTab: WoundType;
  onMainTabClick: (type: WoundType) => void;
}

// --- LOGIC MỚI: SẮP XẾP VÀ TÔ MÀU ---

// 1. Hàm helper để lấy style class cho viền (theo yêu cầu 1)
const getBorderColorClass = (severity: Severity) => {
  switch (severity) {
    case "Mild":
      return styles.borderMild;
    case "Moderate":
      return styles.borderModerate;
    case "Severe":
      return styles.borderSevere;
    default:
      return styles.borderModerate; // Mặc định là màu cam
  }
};

// 2. Hàm helper để gán "trọng số" cho severity (để sắp xếp)
const getSeverityWeight = (severity: Severity) => {
  switch (severity) {
    case "Severe":
      return 3; // Nặng nhất (ở trên)
    case "Moderate":
      return 2;
    case "Mild":
      return 1; // Nhẹ nhất (ở dưới)
    default:
      return 0;
  }
};

// --- Component ---
const AnalysisSidebar = ({
  summaryCounts,
  tabData,
  activeTab,
  onTabClick,
  activeMainTab,
  onMainTabClick,
}: AnalysisSidebarProps) => {
  const { t } = useTranslation(); // <-- 2. KHỞI TẠO HOOK DỊCH
  // 3. Lọc và SẮP XẾP các tab con (theo yêu cầu 2)
  const abrasionTabs = tabData
    .filter((tab) => tab.type === "abrasion")
    .sort(
      (a, b) => getSeverityWeight(b.severity) - getSeverityWeight(a.severity)
    );

  const burnTabs = tabData
    .filter((tab) => tab.type === "burn")
    .sort(
      (a, b) => getSeverityWeight(b.severity) - getSeverityWeight(a.severity)
    );

  const bruiseTabs = tabData
    .filter((tab) => tab.type === "bruise")
    .sort(
      (a, b) => getSeverityWeight(b.severity) - getSeverityWeight(a.severity)
    );

  // 4. SẮP XẾP các nút tab chính (theo yêu cầu 3)
  const allTabs: { type: WoundType; tabs: Tab[]; label: string }[] = [
    { type: "abrasion", tabs: abrasionTabs, label: "Abrasion" },
    { type: "burn", tabs: burnTabs, label: "Burn" },
    { type: "bruise", tabs: bruiseTabs, label: "Bruise" },
  ];

  // Đưa các tab có nội dung (length > 0) lên trước
  const sortedMainTabs = [
    ...allTabs.filter((t) => t.tabs.length > 0),
    ...allTabs.filter((t) => t.tabs.length === 0),
  ];

  // --- 3. LOGIC MỚI: CHỌN DANH SÁCH TAB ĐỂ HIỂN THỊ ---
  let tabsToDisplay: Tab[] = [];
  if (activeMainTab === "abrasion") {
    tabsToDisplay = abrasionTabs;
  } else if (activeMainTab === "burn") {
    tabsToDisplay = burnTabs;
  } else if (activeMainTab === "bruise") {
    tabsToDisplay = bruiseTabs;
  }

  // --- 3. THÊM LOGIC UPLOAD (COPY TỪ OVERVIEW) ---
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log("File selected from Sidebar, navigating to /upload...");
      navigate("/upload", { state: { fileToUpload: file } });
    }
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    fileInputRef.current?.click();
  };
  return (
    <aside className={styles.sidebar}>
      {/* 1. Logo */}
      <Link to="/" className={styles.logoContainer}>
        <img src={Logo} alt="SkinAid Logo" className={styles.logo} />
        <span className={styles.logoText}>SkinAid</span>
      </Link>
      <div className={styles.scrollableContent}>
        {/* 2. Analysis Complete */}
        <div className={styles.completeHeader}>
          <FaCheckCircle />
          <h4>Analysis Complete</h4>
          <p>Your wound has been successfully analyzed</p>
        </div>
        {/* 3. Summary */}
        <div className={styles.summaryCard}>
          <div className={styles.summaryCardHeader}>
            <h5>Summary</h5>
            <p>Detect the total number of wounds in your image</p>
          </div>
          <div className={styles.totalWound}>
            <strong>{summaryCounts.total}</strong>
            <span>Total Wound</span>
          </div>
          <div className={styles.breakdown}>
            <div className={styles.breakdownItem}>
              <strong>{summaryCounts.abrasion}</strong>
              <span>Abrasion</span>
            </div>
            <div className={styles.breakdownItem}>
              <strong>{summaryCounts.burn}</strong>
              <span>Burn</span>
            </div>
            <div className={styles.breakdownItem}>
              <strong>{summaryCounts.bruise}</strong>
              <span>Bruise</span>
            </div>
          </div>
        </div>

        {/* 4. Details (Tabs) - CẬP NHẬT PHẦN NÀY */}
        <div className={styles.detailsTabs}>
          <div className={styles.detailsHeader}>
            <h5>Details</h5>
            <p>List of each type of wound</p>
          </div>

          {/* --- Nav (các nút tab) --- */}
          <nav className={styles.tabNav}>
            {sortedMainTabs.map((mainTab) => (
              <button
                key={mainTab.type}
                className={`${styles.tabNavBtn} ${
                  activeMainTab === mainTab.type ? styles.activeNavBtn : ""
                }`}
                onClick={() => onMainTabClick(mainTab.type)}
                // Vô hiệu hóa nút nếu không có tab con
                // disabled={mainTab.tabs.length === 0}
              >
                {mainTab.label}
              </button>
            ))}
          </nav>

          {/* --- Nội dung tab --- */}
          <div className={styles.tabListContainer}>
            {/* Kiểm tra xem có tab để hiển thị không */} 
            {tabsToDisplay.length > 0 ? (
              // Nếu có, dùng map để render
              tabsToDisplay.map((tab) => (
                <button
                  key={tab.id}
                  className={`${styles.tabItem} ${
                    activeTab === tab.id ? styles.activeTab : ""
                  } ${getBorderColorClass(tab.severity)}`}
                  onClick={() => onTabClick(tab.id)}
                >
                  {tab.title}           
                  <span className={styles[tab.severity.toLowerCase()]}>
                    {tab.severity}           
                  </span>
                </button>
              ))
            ) : (
              // Nếu không, hiển thị thông báo
              <div className={styles.noDataMessage}>
                {t("analysis.no_wounds_found")}
              </div>
            )}
          </div>
        </div>
      </div>
      {/* 5. Upload Button (Luôn ở dưới cùng) */}
      {/* --- 4. CẬP NHẬT NÚT UPLOAD --- */}
      {/* Thêm input ẩn */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept="image/png, image/jpeg, image/jpg"
      />
      <button onClick={handleUploadClick} className={styles.uploadButton}>
        <FaUpload /> Upload Image
      </button>
    </aside>
  );
};

export default AnalysisSidebar;
