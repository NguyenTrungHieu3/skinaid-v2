import React from "react";
import styles from "./AnalysisDetails.module.css";
import { FaCheck } from "react-icons/fa";

interface DetailsProps {
  likelihood: number;
  woundType: string;
  severity: string;
  healingTime: string;
  supportItems: string[];
}

const AnalysisDetails = ({
  likelihood,
  woundType,
  severity,
  healingTime,
  supportItems,
}: DetailsProps) => {
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
      <h3 className={styles.panelTitle}>WOUND DETECTION LIKELIHOOD</h3>

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
          <label>Wound Type</label>
          <div className={styles.detailValue}>{woundType}</div>
        </div>
        <div className={styles.detailItem}>
          <label>Severity</label>
          <div
            className={`${styles.detailValue} ${
              styles[severity.toLowerCase()]
            }`}
          >
            {severity}
          </div>
        </div>
        <div className={styles.detailItem}>
          <label>Est. Healing Time</label>
          <div className={styles.detailValue}>{healingTime}</div>
        </div>
      </div>

      {/* 4. Support Items */}
      <div className={styles.supportItems}>
        <h4 className={styles.supportTitle}>Support Items Identified</h4>
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
