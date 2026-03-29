// src/components/profile/Overview.tsx
import { useRef, useState, useEffect, type ChangeEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import styles from "../../pages/ProfilePage.module.css";
import { FaHistory, FaUpload, FaFileExport } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { getHistory } from "../../services/historyService";
import { useAuth } from "../../contexts/AuthContext";

// Type for analysis from API
type Analysis = {
  id: string;
  type: string;
  location: string;
  severity: "mild" | "moderate" | "severe";
  timestamp: string;
};

// Map severity for display
const mapSeverity = (severity: string): "mild" | "moderate" | "severe" => {
  const s = severity.toLowerCase();
  if (s === "mild") return "mild";
  if (s === "moderate" || s === "medium") return "moderate";
  if (s === "severe") return "severe";
  return "moderate";
};

// Get severity class for styling
const getSeverityClass = (severity: "mild" | "moderate" | "severe") => {
  switch (severity) {
    case "mild":
      return styles.mild;
    case "moderate":
      return styles.medium;
    case "severe":
      return styles.severe;
    default:
      return "";
  }
};

// Format date for display
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return `Today, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  } else if (diffDays === 1) {
    return `Yesterday, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
  }
};

const Overview = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch recent analyses from API
  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    const fetchAnalyses = async () => {
      try {
        setLoading(true);
        const historyData = await getHistory(3, 0); // Get 3 most recent
        
        const events = historyData.events || [];
        const transformed: Analysis[] = events.map((event) => {
          // Lấy wound_types từ significant_wounds
          const woundTypes = event.significant_wounds?.map(w => w.wound_type) || [];
          // Lấy severity đầu tiên hoặc moderate
          const severitySummary = event.significant_wounds?.[0]?.severity || "moderate";
          
          return {
            id: event.analysis_id,
            type: woundTypes.length > 0 
              ? woundTypes[0].charAt(0).toUpperCase() + woundTypes[0].slice(1)
              : "Unknown",
            location: "-", // API doesn't provide location
            severity: mapSeverity(severitySummary),
            timestamp: formatDate(event.analyzed_at || event.created_at),
          };
        });
        
        setAnalyses(transformed);
      } catch (err) {
        setError(t("overview.no_data"));
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyses();
  }, [isAuthenticated, t]);

  /**
   * Xử lý khi người dùng đã chọn file.
   * Đây là lúc chuyển trang.
   */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (file) {
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
          <Link to="/history">{t("overview.view_all")}</Link>
        </div>
        {/* --- DANH SÁCH RENDER ĐỘNG --- */}
        <div className={styles.analysesList}>
          {loading ? (
            <p>{t("map.loading")}</p>
          ) : error ? (
            <p>{error}</p>
          ) : analyses.length === 0 ? (
            <p>{t("overview.no_data")}</p>
          ) : (
            analyses.map((analysis) => (
              <div key={analysis.id} className={styles.analysisItem}>
                <div className={styles.itemInfo}>
                  <h4>{analysis.type}</h4>
                  <p>{analysis.location}</p>
                </div>
                <div className={styles.itemStatus}>
                  <span
                    className={`${styles.statusTag} ${getSeverityClass(
                      analysis.severity
                    )}`}
                  >
                    {analysis.severity.charAt(0).toUpperCase() +
                      analysis.severity.slice(1)}
                  </span>
                  <span className={styles.time}>{analysis.timestamp}</span>
                </div>
                <Link
                  to={`/analysis-result/${analysis.id}`}
                  className={styles.viewLink}
                >
                  {t("overview.view")}
                </Link>
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
