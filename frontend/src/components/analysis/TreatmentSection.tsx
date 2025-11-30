// src/components/analysis/TreatmentSection.tsx
import { useState } from "react";
import styles from "./TreatmentSection.module.css"; // File CSS Module mới
import {
  IoIosArrowDown,
  IoIosArrowUp,
  IoMdCheckmarkCircleOutline,
} from "react-icons/io";
import { LuShieldPlus } from "react-icons/lu";
import { TiWarningOutline } from "react-icons/ti";
import { useTranslation } from "react-i18next";

// 1. Định nghĩa Type cho 'firstaid_snapshot'
// (Dựa trên logic trong file .jsx của bạn)
interface FirstAidSnapshot {
  title?: string;
  steps: string[];
  dos: string[];
  donts: string[];
}
interface TreatmentSectionProps {
  snapshot: FirstAidSnapshot; // Nhận 'snapshot' làm prop
}

const TreatmentSection = ({ snapshot }: TreatmentSectionProps) => {
  const { t } = useTranslation();

  // 2. State và logic được chuyển vào bên trong component này
  const [openSection, setOpenSection] = useState("immediateCare");

  const toggleSection = (section: string) => {
    setOpenSection(openSection === section ? "" : section);
  };

  // 3. Dữ liệu cho các accordion (dựa trên prop 'snapshot')
  const careSections = [
    {
      key: "immediateCare",
      num: 1,
      label: snapshot.title || t("analysis.treatment_immediate_label"),
      subLabel: t("analysis.treatment_immediate_sub_label", {
        step_length: snapshot.steps.length,
      }),
      color: "#F0FDF4", // Green
      colorBorder: "rgba(0, 201, 81, 0.5)",
      steps:
        snapshot.steps.length > 0
          ? snapshot.steps
          : [t("analysis.treatment_not_step")],
    },
    {
      key: "ongoingCare",
      num: 2,
      label: t("analysis.treatment_ongoing_label"),
      subLabel: t("analysis.treatment_ongoing_sub_label", {
        item_length: snapshot.dos.length,
      }),
      color: "#F0F6FE", // Blue
      colorBorder: "rgba(35, 70, 221, 0.5)",
      steps:
        snapshot.dos.length > 0
          ? snapshot.dos
          : [t("analysis.treatment_not_step")],
    },
    {
      key: "notRecommended",
      num: 3,
      label: t("analysis.treatment_not_recommended_label"),
      subLabel: `Những điều cần tránh - ${snapshot.donts.length} mục`,
      color: "#FAE3E2", // Red
      colorBorder: "rgba(182, 30, 27, 0.5)",
      steps:
        snapshot.donts.length > 0
          ? snapshot.donts
          : [t("analysis.treatment_not_step")],
    },
  ];

  return (
    <div className={styles.recommendations}>
      <div className={styles.sectionTitle}>
        <LuShieldPlus className={styles.titleIcon} />
        <h3>{t("analysis.treatment_title")}</h3>
      </div>
      <p className={styles.titleSub}>{t("analysis.treatment_desc")}</p>

      {/* 4. Map qua 'careSections' để render accordions */}
      {careSections.map((section) => (
        <div
          key={section.key}
          className={`${styles.careSection} ${
            openSection === section.key ? styles.open : ""
          }`}
          style={{ backgroundColor: `${section.color}22` }} // Nền nhạt
        >
          <div
            className={styles.careHeader}
            style={{ backgroundColor: section.color }}
            onClick={() => toggleSection(section.key)}
          >
            <div className={styles.headerLeft}>
              <span
                className={`${styles.careNumber} ${
                  styles[`num-${section.num}`]
                }`}
              >
                {section.num}
              </span>
              <div className={styles.careInfo}>
                <strong>{section.label}</strong>
                <p className={styles.careSub}>{section.subLabel}</p>
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
              className={styles.careContent}
              style={{ backgroundColor: section.color }}
            >
              {section.steps.map((step, i) => (
                <li
                  key={i}
                  style={{ border: `1px solid ${section.colorBorder}` }}
                >
                  {/* Icon động dựa trên 'num' */}
                  {section.num === 1 ? (
                    <span className={styles.stepNumberIcon}>{i + 1}</span>
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
  );
};

export default TreatmentSection;
