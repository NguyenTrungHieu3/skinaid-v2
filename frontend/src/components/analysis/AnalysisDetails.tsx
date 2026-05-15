import styles from "./AnalysisDetails.module.css";
import { FaCheck } from "react-icons/fa";
import { useTranslation } from "react-i18next";

interface DetailsProps {
  likelihood: number;
  woundType: string;
  subType?: string | null; // <-- 1. Thêm prop này (có thể null hoặc undefined)
  severity: string;
  healingTime: string;
  supportItems: string[];
}

const capitalize = (str: string) =>
  str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();

const AnalysisDetails = ({
  likelihood,
  woundType,
  subType,
  severity,
  healingTime,
  supportItems,
}: DetailsProps) => {
  const { t } = useTranslation();
  // Tính toán góc xoay cho vòng gauge
  // (likelihood / 100) * 180 độ
  const gaugeRotation = (likelihood / 100) * 180;

  // --- 1. THÊM HÀM LOGIC ĐỂ CHỌN MÀU ---
  const getGaugeColorClass = (value: number) => {
    if (value <= 30) {
      return styles.gaugeRed; // 0-30% là Đỏ
    }
    if (value <= 65) {
      return styles.gaugeYellow; // 30-65% là Vàng
    }
    return styles.gaugeGreen; // 65-100% là Xanh (mặc định)
  };

  return (
    <div className={styles.detailsCard}>
      {/* 1. Tiêu đề Likelihood */}
      <h3 className={styles.panelTitle}>{t("analysis.detail_title")}</h3>

      {/* 2. Vòng Gauge */}
      <div className={styles.gaugeContainer}>
        <div
          className={`${styles.gaugeBackground} ${getGaugeColorClass(
            likelihood
          )}`}
        ></div>
        <div
          className={styles.gaugeFill}
          style={{ transform: `rotate(${gaugeRotation}deg)` }}
        ></div>
        <div className={styles.gaugeCover}>
          <strong>{Math.round(likelihood)}%</strong>
        </div>
      </div>

      {/* 3. Grid chi tiết */}
      <div className={styles.detailsGrid}>
        <div className={styles.detailItem}>
          <label>{t("analysis.detail_wound")}</label>
          <div className={styles.detailValue}>
            {t(`analysis.wound_type_uppercase.${capitalize(woundType)}`)}
            {subType && <span> - {t(`analysis.wound_sub.${subType}`)}</span>}
          </div>
        </div>
        <div className={styles.detailItem}>
          <label>{t("analysis.detail_severity")}</label>
          <div
            className={`${styles.detailValue} ${
              styles[severity.toLowerCase()]
            }`}
          >
            {t(`analysis.severity.${capitalize(severity)}`)}
          </div>
        </div>
        <div className={styles.detailItem}>
          <label>{t("analysis.detail_healing_time")}</label>
          <div className={styles.detailValue}>
            {severity.toLowerCase() === "general"
              ? t("analysis.healing_time_consult") || "Tham khảo bác sĩ"
              : healingTime && healingTime !== "N/A"
              ? healingTime
              : t("analysis.healing_time_loading") || "Đang tải..."}
          </div>
        </div>
      </div>

      {/* 4. Support Items */}
      <div className={styles.supportItems}>
        <h4 className={styles.supportTitle}>{t("analysis.detail_items")}</h4>
        <ul className={styles.supportList}>
          {supportItems.map((item) => (
            <li key={item}>
              <FaCheck /> {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default AnalysisDetails;
