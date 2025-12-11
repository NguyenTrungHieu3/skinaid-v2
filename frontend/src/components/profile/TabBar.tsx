// src/components/profile/TabBar.tsx
import React from "react";
import styles from "../../pages/ProfilePage.module.css"; // Dùng chung file CSS
import { FaChevronLeft, FaChevronRight } from "react-icons/fa";
import { useTranslation } from "react-i18next";
// Định nghĩa kiểu dữ liệu cho props
type TabBarProps = {
  activeTab: string;
  onTabChange: (tab: string) => void;
};

// Định nghĩa thứ tự các tab
const TABS = ["personalInfo", "settings"];

const TabBar: React.FC<TabBarProps> = ({ activeTab, onTabChange }) => {
  // Tìm index của tab hiện tại
  const currentIndex = TABS.indexOf(activeTab);

  const { t } = useTranslation();

  // Xử lý logic cho nút "Lùi"
  const handlePrev = () => {
    if (currentIndex > 0) {
      onTabChange(TABS[currentIndex - 1]);
    }
  };

  // Xử lý logic cho nút "Tới"
  const handleNext = () => {
    if (currentIndex < TABS.length - 1) {
      onTabChange(TABS[currentIndex + 1]);
    }
  };

  return (
    <nav className={styles.tabsWrapper}>
      <button
        className={`${styles.tabArrow} ${styles.tabArrowPrev}`}
        onClick={handlePrev}
        // Ẩn nếu là tab đầu tiên
        style={{ visibility: currentIndex === 0 ? "hidden" : "visible" }}
      >
        <FaChevronLeft />
      </button>

      {/* Nút Overview
      <button
        className={`${styles.tabButton} ${
          activeTab === "overview" ? styles.active : ""
        }`}
        onClick={() => onTabChange("overview")}
      >
        {t("overview.title")}
      </button> */}

      {/* Nút Personal Info */}
      <button
        className={`${styles.tabButton} ${
          activeTab === "personalInfo" ? styles.active : ""
        }`}
        onClick={() => onTabChange("personalInfo")}
      >
        {t("personalInfo.title")}
      </button>

      {/* Nút Settings */}
      <button
        className={`${styles.tabButton} ${
          activeTab === "settings" ? styles.active : ""
        }`}
        onClick={() => onTabChange("settings")}
      >
        {t("settings.title")}
      </button>

      {/* NÚT TỚI (chỉ hiển thị trên mobile) */}
      <button
        className={`${styles.tabArrow} ${styles.tabArrowNext}`}
        onClick={handleNext}
        // Ẩn nếu là tab cuối cùng
        style={{
          visibility: currentIndex === TABS.length - 1 ? "hidden" : "visible",
        }}
      >
        <FaChevronRight />
      </button>
    </nav>
  );
};

export default TabBar;
