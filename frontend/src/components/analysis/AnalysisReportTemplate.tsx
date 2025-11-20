// src/components/analysis/AnalysisReportTemplate.tsx
import React, { useState } from "react";
import styles from "./AnalysisReportTemplate.module.css";
import { type SignificantWound } from "../../services/aiService";
import { type UserProfileResponse } from "../../services/profileService";
import Logo from "../../assets/images/general/logo.png";
interface AnalysisReportTemplateProps {
  wounds: SignificantWound[]; // <-- SỬA: Nhận vào mảng
  imageUrl: string;
  reportId: string;
  fileName?: string;
  analyzedAt?: string;
  // --- THÊM PROP NÀY ---
  userProfile: UserProfileResponse | null;
}

const AnalysisReportTemplate = ({
  wounds,
  imageUrl,
  reportId,
  fileName,
  analyzedAt,
  userProfile,
}: AnalysisReportTemplateProps) => {
  const [imgDimensions, setImgDimensions] = useState<{
    w: number;
    h: number;
  } | null>(null);

  const reportDate = analyzedAt
    ? new Date(analyzedAt).toLocaleDateString("vi-VN")
    : new Date().toLocaleDateString("vi-VN");

  // 2. Hàm xử lý khi ảnh load xong để lấy kích thước
  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    // Chỉ cần set 1 lần vì tất cả vết thương dùng chung 1 ảnh gốc
    if (!imgDimensions) {
      setImgDimensions({
        w: e.currentTarget.naturalWidth,
        h: e.currentTarget.naturalHeight,
      });
    }
  };

  // 3. Hàm tính toán Style cho Box và Label (Giống hệt AnalyzedImage)
  const getBoundingBoxStyles = (wound: SignificantWound) => {
    if (!imgDimensions || !wound.bounding_box) {
      return { boxStyle: { display: "none" }, labelStyle: { display: "none" } };
    }

    const { x, y, width, height } = wound.bounding_box;

    // Tính %
    const topPct = (y / imgDimensions.h) * 100;
    const leftPct = (x / imgDimensions.w) * 100;
    const widthPct = (width / imgDimensions.w) * 100;
    const heightPct = (height / imgDimensions.h) * 100;

    const boxStyle: React.CSSProperties = {
      top: `${topPct}%`,
      left: `${leftPct}%`,
      width: `${widthPct}%`,
      height: `${heightPct}%`,
    };

    // Logic nhãn thông minh (lật vào trong nếu sát mép trên)
    let labelStyle: React.CSSProperties = {};
    if (topPct < 5) {
      labelStyle = {
        top: "0px",
        left: "0px",
        transform: "translate(0, 0)",
        borderRadius: "0 0 4px 0",
      };
    } else {
      labelStyle = {
        bottom: "100%",
        left: "-2px",
        marginBottom: "0px",
        borderRadius: "4px 4px 0 0",
      };
    }

    return { boxStyle, labelStyle };
  };

  // Hàm render từng trang báo cáo
  const renderWoundPage = (wound: SignificantWound, index: number) => {
    const { firstaid_snapshot } = wound;

    // Lấy style cho vết thương hiện tại
    const { boxStyle, labelStyle } = getBoundingBoxStyles(wound);
    const labelText = `${wound.wound_type} ${(
      wound.confidence_score * 100
    ).toFixed(0)}%`;

    return (
      // Thêm class 'pdf-page-to-print' để html2canvas nhận diện
      <div key={index} className={`${styles.container} pdf-page-to-print`}>
        {/* --- HEADER (ĐÃ CẬP NHẬT) --- */}
        <div className={styles.header}>
          {/* Khối Brand: Logo + SkinAid + Medical Report */}
          <div className={styles.brandWrapper}>
            {/* Logo nằm trước */}
            <img src={Logo} alt="SkinAid Logo" className={styles.brandLogo} />

            <div className={styles.brandTextGroup}>
              <h1 className={styles.brandTitle}>
                Skin<span className={styles.brandTitleSub}>Aid</span>
              </h1>
              <h2 className={styles.reportTitle}>MEDICAL REPORT</h2>
              <p className={styles.brandSubtitle}>
                AI-Powered Wound Assessment System
              </p>
            </div>
          </div>

          {/* Khối Meta: Bảng 2 cột không viền */}
          <div className={styles.metaWrapper}>
            <table className={styles.metaTable}>
              <tbody>
                <tr>
                  <td className={styles.metaLabel}>Report ID:</td>
                  <td className={styles.metaValue}>{reportId}</td>
                </tr>
                <tr>
                  <td className={styles.metaLabel}>Date:</td>
                  <td className={styles.metaValue}>{reportDate}</td>
                </tr>
                {fileName && (
                  <tr>
                    <td className={styles.metaLabel}>Source:</td>
                    <td className={styles.metaValue}>{fileName}</td>
                  </tr>
                )}
                <tr>
                  <td className={styles.metaLabel}>Page:</td>
                  <td className={styles.metaValue}>
                    {index + 1}/{wounds.length}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* --- THÊM PHẦN THÔNG TIN BỆNH NHÂN --- */}
        {/* Chỉ hiển thị nếu có userProfile */}
        {userProfile && (
          <div className={styles.patientInfoSection}>
            <div className={styles.patientInfoGrid}>
              <div className={styles.pItem}>
                <span className={styles.pLabel}>Patient Name:</span>
                <span className={styles.pValue}>
                  {userProfile.full_name || "N/A"}
                </span>
              </div>
              <div className={styles.pItem}>
                <span className={styles.pLabel}>Gender:</span>
                <span className={styles.pValue}>
                  {userProfile.gender_display || "N/A"}
                </span>
              </div>
              <div className={styles.pItem}>
                <span className={styles.pLabel}>Day of Birth:</span>
                <span className={styles.pValue}>
                  {userProfile.age ? `${userProfile.date_of_birth}` : "N/A"}
                </span>
              </div>
              <div className={styles.pItem}>
                <span className={styles.pLabel}>Age:</span>
                <span className={styles.pValue}>
                  {userProfile.age ? `${userProfile.age}` : "N/A"}
                </span>
              </div>
              <div className={styles.pItem}>
                <span className={styles.pLabel}>Phone:</span>
                <span className={styles.pValue}>
                  {userProfile.phone || "N/A"}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className={styles.divider} />

        {/* --- SECTION 1: CLINICAL ASSESSMENT --- */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>1. Clinical Assessment</h2>

          <div className={styles.assessmentGrid}>
            {/* Cột Hình ảnh */}
            <div className={styles.imageColumn}>
              <div className={styles.imageWrapper}>
                <img
                  src={imageUrl}
                  alt="Analyzed Wound"
                  crossOrigin="anonymous"
                  className={styles.woundImage}
                  onLoad={handleImageLoad}
                />

                {/* --- VẼ BOUNDING BOX ĐÈ LÊN --- */}
                {imgDimensions && (
                  <div className={styles.boundingBox} style={boxStyle}>
                    <span
                      className={styles.boundingBoxLabel}
                      style={labelStyle}
                    >
                      {labelText}
                    </span>
                  </div>
                )}
              </div>
              <div className={styles.imageCaption}>
                Identified Region: {wound.wound_type.toUpperCase()}Processed
                Analysis Image
              </div>
            </div>

            {/* Cột Thông số */}
            <div className={styles.metricsColumn}>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Primary Diagnosis:</span>
                <span className={styles.metricValueLarge}>
                  {wound.wound_type.toUpperCase()}
                </span>
              </div>

              {wound.sub_type && (
                <div className={styles.metricRow}>
                  <span className={styles.metricLabel}>Sub-type:</span>
                  <span className={styles.metricValue}>{wound.sub_type}</span>
                </div>
              )}

              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Severity Level:</span>
                <span
                  className={`${styles.severityBadge} ${
                    styles[wound.severity.toLowerCase()]
                  }`}
                >
                  {wound.severity}
                </span>
              </div>

              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>AI Confidence:</span>
                <span className={styles.metricValue}>
                  {(wound.confidence_score * 100).toFixed(1)}%
                </span>
              </div>

              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Est. Healing Time:</span>
                <span className={styles.metricValue}>
                  {firstaid_snapshot.estimated_healing_time || "Varied"}
                </span>
              </div>
            </div>
          </div>

          {/* Mô tả & Cảnh báo */}
          <div className={styles.diagnosisDetails}>
            <p className={styles.description}>
              <strong>Description:</strong> {firstaid_snapshot.description}
            </p>

            {firstaid_snapshot.warnings &&
              firstaid_snapshot.warnings.length > 0 && (
                <div className={styles.warningBox}>
                  <strong className={styles.warningTitle}>
                    ⚠️ CRITICAL WARNINGS:
                  </strong>
                  <ul className={styles.warningList}>
                    {firstaid_snapshot.warnings.map((warn, idx) => (
                      <li key={idx}>{warn}</li>
                    ))}
                  </ul>
                </div>
              )}
          </div>
        </div>

        {/* --- SECTION 2: IMMEDIATE ACTION PLAN --- */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>2. Immediate First Aid</h2>
          <div className={styles.stepsContainer}>
            <h3 className={styles.subHeader}>
              {firstaid_snapshot.title || "Step-by-step Instructions"}
            </h3>
            <ol className={styles.stepList}>
              {firstaid_snapshot.steps.map((step, idx) => (
                <li key={idx} className={styles.stepItem}>
                  <span className={styles.stepNumber}>{idx + 1}</span>
                  <span className={styles.stepText}>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>

        {/* --- SECTION 3: CARE GUIDELINES --- */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>3. Care Guidelines</h2>
          <div className={styles.gridTwo}>
            {/* DOs */}
            <div className={`${styles.guidelineBox} ${styles.boxDo}`}>
              <h3
                className={styles.guidelineHeader}
                style={{ color: "#27ae60" }}
              >
                ✓ DO (Nên làm)
              </h3>
              <ul className={styles.checkList}>
                {firstaid_snapshot.dos && firstaid_snapshot.dos.length > 0 ? (
                  firstaid_snapshot.dos.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))
                ) : (
                  <li>Follow general hygiene practices.</li>
                )}
              </ul>
            </div>

            {/* DON'Ts */}
            <div className={`${styles.guidelineBox} ${styles.boxDont}`}>
              <h3
                className={styles.guidelineHeader}
                style={{ color: "#c0392b" }}
              >
                ✕ DON'T (Không nên)
              </h3>
              <ul className={styles.crossList}>
                {firstaid_snapshot.donts &&
                firstaid_snapshot.donts.length > 0 ? (
                  firstaid_snapshot.donts.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))
                ) : (
                  <li>Do not ignore infection signs.</li>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* --- SECTION 4: SUPPLIES --- */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>4. Recommended Supplies</h2>
          <div className={styles.suppliesContainer}>
            {firstaid_snapshot.supplies_needed &&
            firstaid_snapshot.supplies_needed.length > 0 ? (
              firstaid_snapshot.supplies_needed.map((item, i) => (
                <span key={i} className={styles.supplyTag}>
                  {item}
                </span>
              ))
            ) : (
              <span>Basic first aid kit recommended.</span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div
      id="skinaid-pdf-wrapper"
      style={{ position: "absolute", top: 0, left: "-9999px" }}
    >
      {wounds.map((wound, index) => renderWoundPage(wound, index))}
    </div>
  );
};

export default AnalysisReportTemplate;
