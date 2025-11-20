// src/components/analysis/DownloadModal.tsx
import React, { useState, useEffect } from "react";
import styles from "./DownloadModal.module.css";
import { FaFilePdf, FaFileCsv, FaTimes } from "react-icons/fa";
import { type SignificantWound } from "../../services/aiService";

interface DownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownload: (format: "pdf" | "csv", selectedIndices: number[]) => void; // Thêm selectedIndices
  wounds: SignificantWound[]; // Nhận danh sách vết thương
}

const DownloadModal = ({
  isOpen,
  onClose,
  onDownload,
  wounds,
}: DownloadModalProps) => {
  const [selectedFormat, setSelectedFormat] = useState<"pdf" | "csv">("pdf");
  // State lưu danh sách index các vết thương được chọn
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);

  // Khi mở modal, mặc định chọn tất cả
  useEffect(() => {
    if (isOpen && wounds.length > 0) {
      setSelectedIndices(wounds.map((_, index) => index));
    }
  }, [isOpen, wounds]);

  if (!isOpen) return null;

  const handleCheckboxChange = (index: number) => {
    setSelectedIndices((prev) => {
      if (prev.includes(index)) {
        // Bỏ chọn (nhưng không cho phép bỏ chọn hết, ít nhất phải có 1)
        if (prev.length === 1) return prev;
        return prev.filter((i) => i !== index);
      } else {
        // Chọn thêm
        return [...prev, index];
      }
    });
  };

  const handleConfirm = () => {
    onDownload(selectedFormat, selectedIndices);
    onClose();
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h3>Download Report</h3>
          <button onClick={onClose} className={styles.closeBtn}>
            <FaTimes />
          </button>
        </div>

        <p className={styles.subtitle}>Select the format you want to export:</p>

        {/* Format Selection */}
        <div className={styles.options}>
          {/* Option PDF */}
          <div
            className={`${styles.option} ${
              selectedFormat === "pdf" ? styles.selected : ""
            }`}
            onClick={() => setSelectedFormat("pdf")}
          >
            <div className={styles.iconWrapper}>
              <FaFilePdf size={24} color="#e74c3c" />
            </div>
            <div className={styles.optionInfo}>
              <strong>PDF Document</strong>
              <span>Best for sharing and printing.</span>
            </div>
            <div className={styles.radio}>
              <div
                className={selectedFormat === "pdf" ? styles.radioInner : ""}
              ></div>
            </div>
          </div>

          {/* Option CSV (Tạm disable logic chọn vết thương nếu là CSV nếu muốn) */}
          {/* ... Giữ nguyên phần CSV cũ ... */}
        </div>

        {/* --- LOGIC LIST VẾT THƯƠNG (Chỉ hiện nếu có >= 2 vết) --- */}
        {wounds.length > 1 && selectedFormat === "pdf" && (
          <div className={styles.woundSelection}>
            <h4 style={{ marginBottom: "10px", color: "#333" }}>
              Select wounds to include:
            </h4>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                maxHeight: "150px",
                overflowY: "auto",
              }}
            >
              {wounds.map((wound, idx) => (
                <label
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    cursor: "pointer",
                    gap: "8px",
                    fontSize: "14px",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedIndices.includes(idx)}
                    onChange={() => handleCheckboxChange(idx)}
                    style={{
                      accentColor: "#3498db",
                      width: "16px",
                      height: "16px",
                    }}
                  />
                  <span>
                    {/* Hiển thị tên: WoundType + Index (ví dụ: Abrasion 1) */}
                    <strong>
                      {wound.wound_type.charAt(0).toUpperCase() +
                        wound.wound_type.slice(1)}
                    </strong>
                    &nbsp;- {wound.severity} (
                    {(wound.confidence_score * 100).toFixed(0)}%)
                  </span>
                </label>
              ))}
            </div>
            <div style={{ fontSize: "12px", color: "#888", marginTop: "5px" }}>
              {selectedIndices.length === wounds.length
                ? "Full report will be generated."
                : "Custom report with selected wounds."}
            </div>
          </div>
        )}

        <div className={styles.actions}>
          <button onClick={onClose} className={styles.btnCancel}>
            Cancel
          </button>
          <button onClick={handleConfirm} className={styles.btnDownload}>
            Download {selectedFormat.toUpperCase()}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DownloadModal;
