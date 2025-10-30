import React, { useState, useMemo } from "react";
import { useLocation, Navigate } from "react-router-dom";
import "../../assets/styles/AnalysisResults.scss";
// import AnhDaND from "../../assets/images/anhDaNhanDien.png";
import {
  IoMdCheckmarkCircleOutline,
  IoMdCloudDownload,
  IoMdShare,
  IoIosArrowDown,
  IoIosArrowUp,
} from "react-icons/io";
import { LuCamera, LuShieldPlus } from "react-icons/lu";
import { FaRegSave } from "react-icons/fa";
import { FaChartLine } from "react-icons/fa6";
import { MdErrorOutline } from "react-icons/md";
import { TiWarningOutline } from "react-icons/ti";
import { BiCommentDetail } from "react-icons/bi";

const mapWoundsForUI = (significant_wounds) => {
  const woundCounts = {};

  return (significant_wounds || []).map((wound, index) => {
    const type = wound.wound_type || "wound";

    const count = (woundCounts[type] || 0) + 1;
    woundCounts[type] = count;

    const label = `${type.charAt(0).toUpperCase() + type.slice(1)} #${count}`;

    return {
      id: `${type}_${index}`,
      label: label,
      level: wound.severity || "N/A",
      type: type,
      original_index: index,
    };
  });
};

const getWoundCounts = (significant_wounds) => {
  const counts = {};

  (significant_wounds || []).forEach((wound) => {
    const type = wound.wound_type || "unknown";

    const capitalizedKey = type.charAt(0).toUpperCase() + type.slice(1) + "s";

    counts[capitalizedKey] = (counts[capitalizedKey] || 0) + 1;
  });
  return counts;
};

const AnalysisResultsForm = () => {
  const location = useLocation();
  const { fileUrl, result } = location.state || {};

  // Tính toán data (nên dùng useMemo để tối ưu)
  const detectedWounds = useMemo(() => {
    return mapWoundsForUI(result?.significant_wounds || []);
  }, [result]);

  // Khởi tạo state (sau khi có detectedWounds)
  const [activeWoundID, setActiveWoundID] = useState(
    detectedWounds[0]?.id || null
  );

  const [openSection, setOpenSection] = useState("immediateCare");

  if (!result) {
    console.warn("Không có dữ liệu analysis. Điều hướng về trang chủ.");
    return <Navigate to="/upload" replace />;
  }

  // --- TÍNH TOÁN DỮ LIỆU ĐỘNG CHO RENDER ---
  // (Code sẽ chạy lại mỗi khi activeWoundID thay đổi)

  // 1. Lấy data tóm tắt
  const summary = {
    total_wounds: result.total_detections || 0,
    wound_counts: getWoundCounts(result.significant_wounds || []),
    // Dùng cờ 'is_wound_detected' từ API
    is_wound_detected: result.is_wound_detected,
    high_severity_detected:
      result.primary_severity === "severe" ||
      result.primary_severity === "high",
    high_severity_message:
      "Phát hiện vết thương ở mức độ nghiêm trọng. " +
      "Vui lòng tuân thủ khuyến nghị sơ cứu cẩn thận.",
  };

  // 2. Lấy chi tiết vết thương đang chọn
  const activeWoundUIInfo = detectedWounds.find((w) => w.id === activeWoundID);

  const activeWoundApiData = activeWoundUIInfo
    ? // Lấy data gốc từ mảng significant_wounds
      result.significant_wounds[activeWoundUIInfo.original_index]
    : { confidence_score: 0, wound_type: "N/A", severity: "N/A" };

  const snapshot = activeWoundApiData.firstaid_snapshot || {
    title: "Không có hướng dẫn",
    steps: [],
    dos: [],
    donts: [],
    supplies_needed: [],
    estimated_healing_time: null,
  };

  // 3. Lấy chi tiết cho box "Details"
  const abrasionDetails = {
    inConfidence: `${(activeWoundApiData.confidence_score * 100).toFixed(0)}%`,
    woundType: activeWoundApiData.wound_type,
    sensitivity: activeWoundApiData.severity, // Ánh xạ severity sang sensitivity
    estimated_healing_time: snapshot.estimated_healing_time || "Chưa có dự kiến",
    supplies_needed:
      snapshot.supplies_needed && snapshot.supplies_needed.length > 0
        ? snapshot.supplies_needed
        : ["Không yêu cầu vật dụng cụ thể"],
  };

  // 5. Lấy Metadata
  const metadata = {
    timestamp: result.analyzed_at,
    analysis_id: result.analysis_id,
  };

  // 6. TẠO KHUYẾN NGHỊ ĐỘNG (dựa trên snapshot)
  const toggleSection = (section) => {
    setOpenSection(openSection === section ? null : section);
  };

  // const immediateCareData = {
  //   key: "immediateCare",
  //   num: 1,
  //   label: snapshot.title || "Các bước sơ cứu",
  //   subLabel: `Right Now – ${snapshot.steps.length} steps`,
  //   color: "#F0FDF4",
  //   colorBorder: "rgba(0, 201, 81, 0.5)",
  //   steps:
  //     snapshot.steps.length > 0
  //       ? snapshot.steps
  //       : ["Không có hướng dẫn cụ thể."],
  // };

  // const ongoingCareData = {
  //   key: "ongoingCare",
  //   num: 2,
  //   label: "Ongoing Care (Daily)",
  //   subLabel: `Daily routine – ${snapshot.dos.length} steps`,
  //   color: "#F0F6FE",
  //   colorBorder: "rgba(35, 70, 221, 0.5)",
  //   steps:
  //     snapshot.dos.length > 0 ? snapshot.dos : ["Không có hướng dẫn cụ thể."],
  // };

  // const notRecommendedData = {
  //   key: "notRecommended",
  //   num: 3,
  //   label: "Not Recommended",
  //   subLabel: `Things to avoid – ${snapshot.dos.length} items`,
  //   color: "#FAE3E2",
  //   colorBorder: "rgba(182, 30, 27, 0.5)",
  //   steps:
  //     snapshot.dos.length > 0 ? snapshot.dos : ["Không có hướng dẫn cụ thể."],
  // };

  // const careSections = [immediateCareData, ongoingCareData, notRecommendedData]; // Data for the "Detected Wounds" filter buttons

  const careSections = [
    {
      key: "immediateCare",
      num: 1,
      label: snapshot.title || "Các bước sơ cứu",
      subLabel: `Các bước cần làm ngay - ${snapshot.steps.length} bước`,
      color: "#F0FDF4",
      colorBorder: "rgba(0, 201, 81, 0.5)",
      steps:
        snapshot.steps.length > 0
          ? snapshot.steps
          : ["Không có hướng dẫn cụ thể."],
    },
    {
      key: "ongoingCare",
      num: 2,
      label: "Ongoing Care (Daily Care)",
      subLabel: `Những điều nên làm - ${snapshot.dos.length} mục`,
      color: "#F0F6FE",
      colorBorder: "rgba(35, 70, 221, 0.5)",
      steps:
        snapshot.dos.length > 0 ? snapshot.dos : ["Không có hướng dẫn cụ thể."],
    },
    {
      key: "notRecommended",
      num: 3,
      label: "Not recommend",
      // ✅ SỬA LỖI 4: Dùng 'donts.length'
      subLabel: `Những điều cần tránh - ${snapshot.donts.length} mục`,
      color: "#FAE3E2",
      colorBorder: "rgba(182, 30, 27, 0.5)",
      // ✅ SỬA LỖI 4: Dùng 'donts'
      steps:
        snapshot.donts.length > 0
          ? snapshot.donts
          : ["Không có hướng dẫn cụ thể."],
    },
  ];

  // 7. Hàm đổi màu
  const getWoundColorClass = (level) => {
    switch (level?.toLowerCase()) {
      case "mild":
        return "level-1";
      case "moderate":
        return "level-2";
      case "severe":
      case "high":
      case "critical":
        return "level-3";
      default:
        return "";
    }
  };

  return (
    <div className="analysis-page">
      <div className="analysis-complete">
        <div className="analysis-complete-banner">
          <IoMdCheckmarkCircleOutline className="icon-checkmark" />
          <div className="analysis-complete-title">
            <p>Analysis Complete</p>
            <p className="sub-text">
              {summary.total_wounds > 1
                ? "Multiple wounds detected"
                : "Wound detected"}
            </p>
          </div>
        </div>

        <div className="analysis-summary-box">
          <div className="analysis-summary-top">
            <div className="analysis-summary-content">
              <h3>Analysis Summary</h3>
              {/* Kiểm tra cờ 'is_wound_detected' */}
              {!summary.is_wound_detected ? (
                <p className="wound-count-text">
                  Không phát hiện vết thương nào.
                </p>
              ) : (
                <>
                  <p className="wound-count-text">
                    Detect the total number of wounds in your image:
                  </p>
                  <div className="wound-counts">
                    {Object.entries(summary.wound_counts).map(
                      ([type, count]) => (
                        <span key={type} className="type-count">
                          {type} ({count})
                        </span>
                      )
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="number-wound">
              <span>{summary.total_wounds}</span>
              <p>Wound</p>
            </div>
          </div>

          {summary.high_severity_detected && (
            <div className="high-severity-warning">
              <TiWarningOutline className="warning-icon" />
              <div className="warning-content">
                <p className="warning-title">High Severity Wound Detected</p>
                <p className="warning-message">
                  {summary.high_severity_message}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
      {/* ===== Action Buttons (tách riêng, nằm dưới) ===== */}
      <div className="action-buttons">
        <button>
          <FaRegSave className="btn-icon" />
          Save to Wound History
        </button>

        <button>
          <FaChartLine className="btn-icon" />
          Track Progress
        </button>

        <button>
          <IoMdCloudDownload className="btn-icon" />
          Download Report
        </button>

        <button>
          <IoMdShare className="btn-icon" />
          Share
        </button>
      </div>

      <div className="content-section">
        <div className="analyzed-image">
          <div className="section-title">
            <LuCamera className="title-icon" />
            <h3>Analyzed Image</h3>
          </div>
          <img src={result.image_url || fileUrl} alt="Analyzed wound" />

          <p className="detected-wounds-label">
            Detected Wounds (click to select):
          </p>
          <div className="wound-filter-buttons">
            {detectedWounds.map((wound) => (
              <button
                key={wound.id}
                className={`wound-filter-btn ${getWoundColorClass(
                  wound.level
                )} ${activeWoundID === wound.id ? "active" : ""}`}
                // ✅ SỬA LỖI TYPO: 'setActiveWoundID'
                onClick={() => setActiveWoundID(wound.id)}
              >
                {wound.label}
                <span className="wound-level">{wound.level}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="details-notes-section">
          <div className="analysis-details">
            <div className="notes-title">
              <BiCommentDetail className="title-icon" />
              <h3>
                Details:
                {/* ✅ SỬA LỖI TYPO: 'activeWoundID' */}
                {detectedWounds.find((w) => w.id === activeWoundID)?.label ||
                  "No wound selected"}
              </h3>
            </div>
            {/* Box này giờ đã hoàn toàn động */}
            <div className="detail-row">
              <div className="detail-item-small">
                <label>AI Confidence</label>
                <p className="confidence-value">
                  {abrasionDetails.inConfidence}
                </p>
                <div className="confidence-bar-container">
                  <div
                    className="confidence-bar"
                    style={{ width: abrasionDetails.inConfidence }}
                  ></div>
                </div>
              </div>
              <div className="detail-item-small">
                <label>Wound Type</label>
                <p>{abrasionDetails.woundType}</p>
              </div>
            </div>
            <div className="detail-row">
              <div className="detail-item-small">
                <label>Sensitivity</label>
                <p className="sensitivity-level">
                  {abrasionDetails.sensitivity}
                </p>
              </div>
              <div className="detail-item-small">
                <label>Healing Time</label>
                <p>{abrasionDetails.estimated_healing_time}</p>
              </div>
            </div>
            <div className="observed-characteristics">
              <label>Supplies Needed</label>
              <ul>
                {abrasionDetails.supplies_needed.map((char, i) => (
                  <li key={i}>
                    <IoMdCheckmarkCircleOutline className="list-check-icon" />{" "}
                    {char}
                  </li>
                ))}
              </ul>
            </div>
                     
            <hr />
            <div className="meta-info">
              <p>
                <strong>Analysis Timestamp</strong>
                <br />
                {new Date(metadata.timestamp).toLocaleString()}
              </p>
              <p>
                <strong>Analysis ID</strong>
                <br />
                {metadata.analysis_id}
              </p>
            </div>
          </div>
        </div>

        {/* Box này giờ đã hoàn toàn động */}
        <div className="recommendations">
          <div className="section-title">
            <LuShieldPlus className="title-icon" />
            <h3>Treatment Recommendations</h3>
          </div>
          <p>Follow these evidence-based care guidelines for optimal healing</p>

          {/* Dùng 'careSections' động đã được tính ở trên */}
          {careSections.map((section) => (
            <div
              key={section.key}
              className={`care-section ${
                openSection === section.key ? "open" : ""
              }`}
              style={{ backgroundColor: `${section.color}22` }}
            >
              <div
                className="care-header"
                style={{ backgroundColor: section.color }}
                onClick={() => toggleSection(section.key)}
              >
                <div className="header-left">
                  <span className={`care-number num-${section.num}`}>
                    {section.num}
                  </span>
                  <div className="care-info">
                    <strong>{section.label}</strong>
                    <p className="care-sub">{section.subLabel}</p>
                  </div>
                </div>
                {openSection === section.key ? (
                  <IoIosArrowUp size={18} />
                ) : (
                  <IoIosArrowDown size={18} />
                )}
              </div>

              {openSection === section.key && (
                <ul
                  className="care-content"
                  style={{ backgroundColor: section.color }}
                >
                  {section.steps.map((step, i) => (
                    <li
                      key={i}
                      style={{ border: `1px solid ${section.colorBorder}` }}
                    >
                      {section.num === 1 ? (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: "22px",
                            height: "22px",
                            borderRadius: "50%",
                            backgroundColor: "#00C951",
                            color: "#fff",
                            fontSize: "12px",
                            fontWeight: "bold",
                            flexShrink: 0, // Thêm để icon không bị bóp
                          }}
                        >
                          {i + 1}
                        </span>
                      ) : section.num === 2 ? (
                        <IoMdCheckmarkCircleOutline
                          color="#2346dd"
                          size={20}
                          style={{ flexShrink: 0 }}
                        />
                      ) : (
                        <TiWarningOutline
                          color="#b61e1b"
                          size={20}
                          style={{ flexShrink: 0 }}
                        />
                      )}
                      <span style={{ marginLeft: "8px" }}>{step}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer">
        <strong>
          <MdErrorOutline className="disclaimer-icon" />
          Important Medical Disclaimer
        </strong>

        <p>
          This AI analysis is for informational purposes only and should not
          replace professional medical advice. Always consult with a healthcare
          provider for proper wound assessment and treatment.
        </p>
      </div>
    </div>
  );
};

export default AnalysisResultsForm;
