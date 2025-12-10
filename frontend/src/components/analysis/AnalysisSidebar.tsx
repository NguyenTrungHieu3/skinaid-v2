import { useState } from "react";
import styles from "./AnalysisSidebar.module.css";
import {
  FaCheckCircle,
  FaChevronDown,
  FaChevronUp,
  FaListAlt,
} from "react-icons/fa"; // Thêm icon
import { Link } from "react-router-dom";
import Logo from "../../assets/images/general/logo.png";
import { useTranslation } from "react-i18next";

// ... (Giữ nguyên các interface SummaryCounts, Tab, Props cũ) ...
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

// NEW — Split title → type + number
const parseWoundTitle = (title: string) => {
  const parts = title.split(/[-\s]+/);
  return {
    type: parts[0], // Abrasion
    number: parts[1] || "", // 1
    sub_type: parts.slice(2).join(" ") || "", // Superficial
  };
};

const AnalysisSidebar = ({
  summaryCounts,
  tabData,
  activeTab,
  onTabClick,
  activeMainTab,
  onMainTabClick,
}: AnalysisSidebarProps) => {
  const { t } = useTranslation();

  // --- STATE MỚI: Quản lý đóng mở trên Mobile ---
  const [isMobileExpanded, setIsMobileExpanded] = useState(false);

  // ... (Giữ nguyên logic sắp xếp Tab, handleFileChange) ...
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

  const allTabs = [
    { type: "abrasion" as WoundType, tabs: abrasionTabs, label: "Abrasion" },
    { type: "burn" as WoundType, tabs: burnTabs, label: "Burn" },
    { type: "bruise" as WoundType, tabs: bruiseTabs, label: "Bruise" },
  ];

  const sortedMainTabs = [
    ...allTabs.filter((t) => t.tabs.length > 0),
    ...allTabs.filter((t) => t.tabs.length === 0),
  ];

  let tabsToDisplay: Tab[] = [];
  if (activeMainTab === "abrasion") tabsToDisplay = abrasionTabs;
  else if (activeMainTab === "burn") tabsToDisplay = burnTabs;
  else if (activeMainTab === "bruise") tabsToDisplay = bruiseTabs;

  return (
    <aside
      className={`${styles.sidebar} ${
        isMobileExpanded ? styles.mobileExpanded : ""
      }`}
    >
      {/* Header Mobile: Logo + Toggle Button */}
      <div className={styles.mobileHeaderGroup}>
        <Link to="/" className={styles.logoContainer}>
          <img src={Logo} alt="SkinAid Logo" className={styles.logo} />
          <span className={styles.logoText}>SkinAid</span>
        </Link>
      </div>

      <div className={styles.scrollableContent}>
        {/* 2. Analysis Complete (Chỉ hiện trên Desktop - xem CSS class desktopOnlyBlock) */}
        <div className={`${styles.completeHeader} ${styles.desktopOnlyBlock}`}>
          <FaCheckCircle />
          <h4>{t("analysis.sidebar_complete")}</h4>
        </div>

        {/* 3. MOBILE SUMMARY BLOCK (Mới) */}
        {/* Chỉ hiện trên Mobile. Chứa Icon + Summary + Count */}
        <div
          className={styles.mobileSummaryBlock}
          onClick={() => setIsMobileExpanded(!isMobileExpanded)}
        >
          <div className={styles.summaryBlockLeft}>
            <FaListAlt className={styles.summaryIcon} />
            <span className={styles.summaryLabel}>
              {t("analysis.sidebar_summary")}
            </span>
            {/* Hiển thị số lượng vết thương */}
            <span className={styles.woundCountBadge}>
              {t("analysis.sidebar_wound_count", {
                count: summaryCounts.total,
              })}
            </span>
          </div>
          <div className={styles.summaryBlockRight}>
            {isMobileExpanded ? <FaChevronUp /> : <FaChevronDown />}
          </div>
        </div>

        {/* PHẦN NÀY SẼ BỊ ẨN TRÊN MOBILE KHI THU GỌN */}
        <div className={styles.collapsibleContent}>
          <div className={styles.summaryCard}>
            {/* ... Nội dung Summary giữ nguyên ... */}
            <div className={styles.summaryCardHeader}>
              <h5>{t("analysis.sidebar_summary")}</h5>
              <p>{t("analysis.sidebar_summary_desc")}</p>
            </div>
            <div className={styles.totalWound}>
              <strong>{summaryCounts.total}</strong>
              <span>{t("analysis.sidebar_summary_total")}</span>
            </div>
            <div className={styles.breakdown}>
              <div className={styles.breakdownItem}>
                <strong>{summaryCounts.abrasion}</strong>
                <span>{t("analysis.sidebar_summary_abrasion")}</span>
              </div>
              <div className={styles.breakdownItem}>
                <strong>{summaryCounts.burn}</strong>
                <span>{t("analysis.sidebar_summary_burn")}</span>
              </div>
              <div className={styles.breakdownItem}>
                <strong>{summaryCounts.bruise}</strong>
                <span>{t("analysis.sidebar_summary_bruise")}</span>
              </div>
            </div>
          </div>

          <div className={styles.detailsTabs}>
            <div className={styles.detailsHeader}>
              <h5>{t("analysis.sidebar_details")}</h5>
              <p>{t("analysis.sidebar_details_desc")}</p>
            </div>

            <nav className={styles.tabNav}>
              {sortedMainTabs.map((mainTab) => (
                <button
                  key={mainTab.type}
                  className={`${styles.tabNavBtn} ${
                    activeMainTab === mainTab.type ? styles.activeNavBtn : ""
                  }`}
                  onClick={() => onMainTabClick(mainTab.type)}
                >
                  {t(`analysis.wound_type.${mainTab.type}`)}
                </button>
              ))}
            </nav>

            <div className={styles.tabListContainer}>
              {tabsToDisplay.length > 0 ? (
                tabsToDisplay.map((tab) => {
                  const { type, number, sub_type } = parseWoundTitle(tab.title);

                  return (
                    <button
                      key={tab.id}
                      className={`${styles.tabItem} ${
                        activeTab === tab.id ? styles.activeTab : ""
                      } ${getBorderColorClass(tab.severity)}`}
                      onClick={() => {
                        onTabClick(tab.id);
                        setIsMobileExpanded(false);
                      }}
                    >
                      {t(`analysis.wound_type_uppercase.${type}`)} {number}
                      {sub_type && t(`analysis.wound_sub.${sub_type}`)}
                      <span className={styles[tab.severity.toLowerCase()]}>
                        {t(`analysis.severity.${tab.severity}`)}
                      </span>
                    </button>
                  );
                })
              ) : (
                <div className={styles.noDataMessage}>
                  {t("analysis.sidebar_no_wounds_found")}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default AnalysisSidebar;
